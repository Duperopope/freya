# src/freya/tui.py
from __future__ import annotations

import asyncio
import csv
import datetime as dt
import inspect
import json
import logging
import os
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Deque, cast

from rich.markdown import Markdown
from rich.panel import Panel

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.screen import ModalScreen
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    Static,
    Button,
    RichLog,
    DataTable,
    Select,
    Checkbox,
    TextArea,
    ProgressBar,
    DirectoryTree,
    Input,
)

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter
from .orchestrator import Orchestrator


# -------------------- FREE WEB HELPERS --------------------
def fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Freya/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def wiki_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    params = urllib.parse.urlencode(
        {
            "action": "opensearch",
            "search": query,
            "limit": str(max(1, min(limit, 10))),
            "namespace": "0",
            "format": "json",
        }
    )
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Freya/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8", errors="ignore"))
    titles = data[1] if len(data) > 1 else []
    descs = data[2] if len(data) > 2 else []
    links = data[3] if len(data) > 3 else []
    out: list[dict[str, str]] = []
    for i in range(min(len(titles), limit)):
        out.append(
            {
                "title": str(titles[i]),
                "snippet": str(descs[i]) if i < len(descs) else "",
                "url": str(links[i]) if i < len(links) else "",
            }
        )
    return out


# -------------------- SECURITY: REDACT TOKENS --------------------
_PAT = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bsk-[A-Za-z0-9]+\b"),
]


def redact(text: str) -> str:
    out = text
    for p in _PAT:
        out = p.sub("[REDACTED_SECRET]", out)
    return out


def copy_clipboard_windows(text: str) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
        input=text,
        text=True,
        check=True,
    )


def icon(nerd: str, fallback: str) -> str:
    return nerd if os.environ.get("FREYA_NERD_ICONS", "1") == "1" else fallback


I_CHAT = icon("󰭹", "CHAT")
I_BENCH = icon("󱎴", "BENCH")
I_DEV = icon("󰨞", "BMAD")
I_SET = icon("󰒓", "SET")
I_WATCH = icon("󰔚", "WATCH")
I_COPY = icon("󰆏", "COPY")
I_PLAY = icon("󰐊", "START")
I_STOP = icon("󰓛", "STOP")
I_WEB = icon("󰖟", "WEB")
I_OPEN = icon("󰏌", "OPEN")
I_SAVE = icon("󰆓", "SAVE")
I_EXIT = icon("󰗼", "EXIT")


DEFAULT_CHAT_BASE_FR = """Tu es Freya. Tu réponds en français, de façon claire, structurée et utile.

Sécurité / cadre:
- Légal uniquement.
- Défensif par défaut.
- Si on te demande du contenu illégal/offensif réel, tu refuses et proposes des alternatives défensives.
- Quand tu utilises des infos Web (Cyber Watch / Search), tu cites les URLs.

Style:
- Réponses actionnables.
- Format Markdown.
"""

DEFAULT_HATS_MD = """## Blue Hat (défense)
Blue team défensif: durcissement, patch, audit, SOC, IR. Refuse illégal.

## White Hat (pentest légal)
Pentest légal: méthodo, périmètre, reporting, remédiation. Pas de détails exploitables.

## Grey Hat (research)
Veille CVE, risques, mitigations, PoC high-level. Pas de step-by-step d'exploitation.

## Red Team (simulation autorisée)
Simulation autorisée: threat modeling, MITRE ATT&CK, détection. Refuse illégal/offensif réel.
"""

DEFAULT_ROLE_PROMPTS = {
    "analyst": "Tu es l'Analyst BMAD. Tu produis project-brief.md selon BMAD. Précis, structuré.",
    "pm": "Tu es le PM BMAD. Tu produis PRD.md (FR/NFR/epics).",
    "architect": "Tu es l'Architect BMAD. Tu produis architecture.md (modules, risques, observabilité, sécurité).",
    "po": "Tu es le Product Owner BMAD. Tu shards en epic-*.md propres.",
    "sm": "Tu es le Scrum Master BMAD. Tu produis *.story.md détaillés (AC, steps, tests).",
    "dev": "Tu es le Developer BMAD. Tu codes, tests, respecte les contraintes.",
    "qa": "Tu es le QA BMAD. Tu valides, matrice de traçabilité, quality gates.",
}


class PromptStoreLite:
    def __init__(self, root: Path):
        self.root = root

    def ensure_defaults(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "bmad_roles").mkdir(parents=True, exist_ok=True)

        chat = self.root / "chat_base_fr.md"
        if not chat.exists():
            chat.write_text(DEFAULT_CHAT_BASE_FR, encoding="utf-8")

        hats = self.root / "chat_hat_presets.md"
        if not hats.exists():
            hats.write_text(DEFAULT_HATS_MD, encoding="utf-8")

        for role, txt in DEFAULT_ROLE_PROMPTS.items():
            f = self.root / "bmad_roles" / f"{role}.md"
            if not f.exists():
                f.write_text(txt + "\n", encoding="utf-8")

    def load(self, rel: str) -> str:
        p = self.root / rel
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8", errors="ignore")

    def save(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def list_roles(self) -> list[str]:
        d = self.root / "bmad_roles"
        if not d.exists():
            return []
        return sorted([p.stem for p in d.glob("*.md")])


class GoalPrompt(ModalScreen[str | None]):
    def compose(self) -> ComposeResult:
        yield Container(
            Static("Objectif BMAD (langage naturel) :", id="gp_title"),
            TextArea(id="gp_text"),
            Horizontal(
                Button("Annuler", id="gp_cancel"),
                Button("Lancer", id="gp_ok", variant="primary"),
                id="gp_buttons",
            ),
            id="gp_modal",
        )

    def on_mount(self) -> None:
        ta = self.query_one("#gp_text", TextArea)
        ta.text = ""
        ta.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gp_cancel":
            self.dismiss(None)
        elif event.button.id == "gp_ok":
            txt = (self.query_one("#gp_text", TextArea).text or "").strip()
            self.dismiss(txt if txt else None)


# -------------------- BENCH STATE --------------------
@dataclass
class BenchLiveState:
    running: bool = False
    program: str = "bench-fast"
    phase: str = "—"
    role: str = "—"
    model: str = "—"

    model_i: int = 0
    total_models: int = 1
    step_i: int = 0
    steps_total: int = 1

    last_event: str = ""
    stop_requested: bool = False
    last_state_done: int = 0
    last_state_updated_at: float | None = None

    ticks_seen: int = 0
    events_seen: int = 0

    pending_rows: Deque[tuple[str, str, str, str, str, str]] = field(default_factory=lambda: deque(maxlen=8000))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            j = json.loads(path.read_text(encoding="utf-8"))
            return j if isinstance(j, dict) else {}
    except Exception:
        pass
    return {}


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _pb_set(bar: ProgressBar, *, total: int, progress: int) -> None:
    total = max(1, int(total))
    progress = max(0, min(int(progress), total))
    upd = getattr(bar, "update", None)
    if callable(upd):
        try:
            upd(total=total, progress=progress)
            return
        except Exception:
            pass
    try:
        bar.total = total
        bar.progress = progress
    except Exception:
        pass


class FreyaTUI(App):
    CSS_PATH = "tui.tcss"

    BINDINGS = [
        ("ctrl+enter", "send_chat", "Envoyer"),
        ("ctrl+c", "copy_last", "Copier"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.cfg = FreyaConfig.load()
        self.client = OllamaClient(base_url=self.cfg.ollama.base_url)
        self.router = LLMRouter(self.client)

        self.store = PromptStoreLite(self.cfg.prompts_root)
        self.store.ensure_defaults()

        self.models: list[str] = []
        self.last_assistant: str = ""
        self.output_root: Path = self.cfg.output_root

        self._bench_lock = threading.Lock()
        self._bench = BenchLiveState()

        self._override_by_role: dict[str, str] = self._load_overrides()
        self.selected_artifact: Path | None = None

        self._exiting = False

    # -------------------- forced-save on exit --------------------
    def exit(self, *args: Any, **kwargs: Any) -> None:
        if not self._exiting:
            self._exiting = True
            try:
                with self._bench_lock:
                    self._bench.stop_requested = True
                self._save_everything_best_effort()
            except Exception:
                pass
        return super().exit(*args, **kwargs)

    # -------------------- layout --------------------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="root"):
            with Vertical(id="left"):
                with TabbedContent(id="tabs"):
                    with TabPane(f"{I_CHAT} Chat", id="tab_chat"):
                        yield self._chat_toolbar()
                        yield RichLog(id="chat_log", wrap=True)
                        yield self._chat_composer()

                    with TabPane(f"{I_BENCH} Benchmark", id="tab_bench"):
                        yield self._bench_tab()

                    with TabPane(f"{I_DEV} Webdeveloper (BMAD)", id="tab_bmad"):
                        yield self._bmad_toolbar()
                        yield RichLog(id="bmad_log", wrap=True)

                    with TabPane(f"{I_SET} Settings", id="tab_settings"):
                        yield self._settings_panel()

            with Vertical(id="right"):
                yield Static("Artefacts • Preview", id="art_title")
                yield Static(f"Output: {self.output_root}", id="art_root")
                yield DirectoryTree(self.output_root, id="art_tree")
                yield RichLog(id="art_preview", wrap=True)

        yield Footer()

    # -------------------- UI blocks --------------------
    def _chat_toolbar(self) -> Container:
        return Container(
            Horizontal(
                Static("Hat:", classes="muted"),
                Select([], id="hat_select"),
                Static("Primary:", classes="muted"),
                Select([], id="primary_model"),
                Static("Summ:", classes="muted"),
                Select([], id="summarizer_model"),
                Checkbox("Auto", id="best_models"),
                Button(f"{I_WATCH} Cyber Watch", id="btn_watch", variant="primary"),
                Button(f"{I_WEB} Search", id="btn_search"),
                Button(f"{I_COPY} Copier", id="btn_copy"),
                id="chat_row1",
            ),
            Static("⏳ Freya réfléchit…", id="thinking", classes="hidden"),
            TextArea(id="chat_base_prompt"),
            id="chat_toolbar",
        )

    def _chat_composer(self) -> Container:
        return Container(
            TextArea(id="chat_input"),
            Horizontal(
                Button("Envoyer (Ctrl+Enter)", id="btn_send", variant="primary"),
                Button("Effacer", id="btn_clear"),
                id="chat_actions",
            ),
            id="chat_composer",
        )

    def _settings_panel(self) -> Container:
        roles = self.store.list_roles() or list(DEFAULT_ROLE_PROMPTS.keys())
        return Container(
            Static("Prompts (éditables)", id="set_title"),
            Horizontal(
                Static("BMAD role:", classes="muted"),
                Select([(r, r) for r in roles], id="role_select"),
                Button("Load", id="btn_load_role"),
                Button("Save", id="btn_save_role", variant="primary"),
                id="set_row1",
            ),
            TextArea(id="role_prompt"),
            Static("Web search: gratuit via Wikipedia API (/search ...).", classes="muted"),
            id="settings_panel",
        )

    def _bmad_toolbar(self) -> Container:
        return Container(
            Static("BMAD Studio: lance un cycle BMAD et écrit des artefacts dans Output.", id="bmad_overview"),
            Horizontal(
                Button("Run BMAD…", id="btn_bmad_run", variant="primary"),
                Button("Refresh artefacts", id="btn_refresh_artifacts"),
                Button(f"{I_OPEN} VS Code", id="btn_open_vscode"),
                id="bmad_actions",
            ),
            Horizontal(
                Static("Output:", classes="muted"),
                Input(value=str(self.output_root), id="out_dir"),
                Button("Set", id="btn_set_out", variant="primary"),
                id="bmad_out_row",
            ),
            id="bmad_toolbar",
        )

    def _billboard(self) -> Container:
        return Container(
            Static("Billboard (meilleur modèle par rôle)", id="bb_title"),
            DataTable(id="bb_table"),
            Horizontal(
                Static("Role:", classes="muted"),
                Select([(r, r) for r in ["analyst", "pm", "architect", "po", "sm", "dev", "qa"]], id="ov_role"),
                Static("Model:", classes="muted"),
                Select([], id="ov_model"),
                Button("Apply override", id="btn_apply_override", variant="primary"),
                Button("Save overrides", id="btn_save_overrides"),
                id="bb_controls",
            ),
            id="bench_billboard",
        )

    def _bench_tab(self) -> Container:
        return Container(
            Horizontal(
                Button(f"{I_PLAY} Fast (auto)", id="btn_bench_fast", variant="primary"),
                Button(f"{I_PLAY} Standard (resume)", id="btn_bench_resume_std"),
                Button(f"{I_PLAY} Standard", id="btn_bench_standard"),
                Button(f"{I_PLAY} Advanced", id="btn_bench_advanced"),
                Button(f"{I_STOP} Stop (soft)", id="btn_bench_stop"),
                Button("Apply routing (best)", id="btn_apply_routing"),
                Button("Reload last session", id="btn_reload_state"),
                Button(f"{I_SAVE} Save + {I_EXIT} Exit", id="btn_save_and_exit", variant="warning"),
                id="bench_actions",
            ),
            Static(
                f"cache={self.cfg.cache_root} • reports={self.cfg.managed_root / 'reports'} • backend={self.cfg.ollama.base_url}",
                classes="muted",
            ),
            Container(
                Horizontal(
                    Static("Program:", classes="muted"),
                    Static("—", id="bench_program"),
                    Static("Running:", classes="muted"),
                    Static("no", id="bench_running"),
                    Static("Phase:", classes="muted"),
                    Static("—", id="bench_phase"),
                    Static("Role:", classes="muted"),
                    Static("—", id="bench_role"),
                    Static("Model:", classes="muted"),
                    Static("—", id="bench_model"),
                    id="bench_labels",
                ),
                Horizontal(
                    Static("Models:", classes="muted"),
                    ProgressBar(total=1, id="bench_models_bar"),
                    Static("Steps:", classes="muted"),
                    ProgressBar(total=1, id="bench_steps_bar"),
                    id="bench_bars",
                ),
                Horizontal(
                    Static("Counts:", classes="muted"),
                    Static("models 0/0 • steps 0/0", id="bench_counts"),
                    Static("ticks:", classes="muted"),
                    Static("0", id="bench_ticks"),
                    Static("events:", classes="muted"),
                    Static("0", id="bench_events"),
                    id="bench_counts_line",
                ),
                Horizontal(
                    Static("State:", classes="muted"),
                    Static("—", id="bench_state_path"),
                    Static("done:", classes="muted"),
                    Static("0", id="bench_done"),
                    Static("updated:", classes="muted"),
                    Static("—", id="bench_updated"),
                    Static("event:", classes="muted"),
                    Static("—", id="bench_event"),
                    id="bench_state_line",
                ),
                id="bench_status_block",
            ),
            Static("Live results (ALL model_done rows preserved):", classes="muted"),
            DataTable(id="bench_table"),
            self._billboard(),
            id="bench_tab",
        )

    # -------------------- lifecycle --------------------
    def on_mount(self) -> None:
        try:
            self.models = self.router.list_models()
        except Exception:
            self.models = []
        if not self.models:
            self.models = ["llama3.1:8b"]

        self.query_one("#primary_model", Select).set_options([(m, m) for m in self.models])
        self.query_one("#summarizer_model", Select).set_options([(m, m) for m in self.models])
        self.query_one("#ov_model", Select).set_options([(m, m) for m in self.models])

        self.query_one("#primary_model", Select).value = self._prefer(["dolphin-llama3:8b", "llama3.1:8b", "mistral:7b"])
        self.query_one("#summarizer_model", Select).value = self._prefer(["llama3.1:8b", "mistral:7b"])

        hats = self._hat_options()
        self.query_one("#hat_select", Select).set_options(hats)
        self.query_one("#hat_select", Select).value = hats[0][0]

        self.query_one("#chat_base_prompt", TextArea).text = self.store.load("chat_base_fr.md")
        self._load_role_prompt("analyst")

        bt = self.query_one("#bench_table", DataTable)
        bt.add_columns("role", "phase", "model", "score", "latency_ms", "status")

        models_bar = self.query_one("#bench_models_bar", ProgressBar)
        steps_bar = self.query_one("#bench_steps_bar", ProgressBar)
        for bar in (models_bar, steps_bar):
            bar.styles.width = "1fr"
            bar.styles.height = 1
            bar.styles.min_width = 24

        bb = self.query_one("#bb_table", DataTable)
        bb.add_columns("role", "best_model", "score", "latency_ms", "override")

        self._ensure_output_root()
        self._refresh_tree()

        self._bench_reload_last_session()
        self._bench_load_table_history()
        self.set_interval(0.12, self._bench_tick_ui)

        if os.environ.get("FREYA_AUTOBENCH", "1") == "1":
            self.call_after_refresh(self._bench_autostart_a1)

        self._log_chat("system", "Prêt. Bench auto fast (A1). BMAD dispo via bouton.")

    def _prefer(self, candidates: list[str]) -> str:
        for c in candidates:
            if c in self.models:
                return c
        return self.models[0]

    # -------------------- hats parsing --------------------
    def _hat_options(self) -> list[tuple[str, str]]:
        txt = self.store.load("chat_hat_presets.md")
        names: list[str] = []
        for line in txt.splitlines():
            if line.startswith("## "):
                names.append(line[3:].strip())
        if not names:
            names = ["Blue Hat (défense)"]
        return [(n, n) for n in names]

    def _get_hat_text(self, hat_name: str) -> str:
        txt = self.store.load("chat_hat_presets.md")
        cur = None
        buf: list[str] = []
        sections: dict[str, str] = {}
        for line in txt.splitlines():
            if line.startswith("## "):
                if cur is not None:
                    sections[cur] = "\n".join(buf).strip()
                cur = line[3:].strip()
                buf = []
            else:
                buf.append(line)
        if cur is not None:
            sections[cur] = "\n".join(buf).strip()
        return sections.get(hat_name, "")

    # -------------------- thinking (ONLY ONCE - fixed redeclaration) --------------------
    def _set_thinking(self, on: bool) -> None:
        w = self.query_one("#thinking", Static)
        if on:
            w.remove_class("hidden")
        else:
            w.add_class("hidden")

    # -------------------- chat logging --------------------
    def _log_chat(self, role: str, content: str) -> None:
        log = self.query_one("#chat_log", RichLog)
        ts = dt.datetime.now().strftime("%H:%M:%S")
        content = redact(content)

        if role == "assistant":
            self.last_assistant = content
            log.write(Panel(Markdown(content), title=f"Assistant • {ts}", border_style="cyan"))
        elif role == "user":
            log.write(Panel(Markdown(content), title=f"Vous • {ts}", border_style="green"))
        elif role == "tool":
            log.write(Panel(Markdown(content), title=f"Outil • {ts}", border_style="magenta"))
        else:
            log.write(f"[{role}] {content}")

    def _log_bmad(self, content: str, title: str = "BMAD") -> None:
        log = self.query_one("#bmad_log", RichLog)
        ts = dt.datetime.now().strftime("%H:%M:%S")
        log.write(Panel(Markdown(redact(content)), title=f"{title} • {ts}", border_style="yellow"))

    # -------------------- artifacts tree --------------------
    def _ensure_output_root(self) -> None:
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.query_one("#art_root", Static).update(f"Output: {self.output_root}")

    def _refresh_tree(self) -> None:
        tree = self.query_one("#art_tree", DirectoryTree)
        try:
            tree.path = self.output_root
        except Exception:
            pass

        reload_fn = getattr(tree, "reload", None)
        if callable(reload_fn):
            try:
                res = reload_fn()
                if inspect.isawaitable(res):
                    aw = cast(Awaitable[Any], res)

                    async def _runner() -> None:
                        try:
                            await aw
                        except Exception:
                            pass

                    # asyncio.create_task expects a coroutine object:
                    # https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
                    self.call_after_refresh(lambda: asyncio.create_task(_runner()))
            except Exception:
                pass

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = Path(event.path)
        self.selected_artifact = path
        pr = self.query_one("#art_preview", RichLog)
        pr.clear()
        try:
            if path.suffix.lower() == ".md":
                text = path.read_text(encoding="utf-8", errors="ignore")
                pr.write(Panel(Markdown(redact(text)), title=path.name, border_style="white"))
            else:
                pr.write(Panel(Markdown(f"`{path}`"), title=path.name, border_style="white"))
        except Exception as e:
            pr.write(Panel(Markdown(f"Erreur: {type(e).__name__}: {e}"), title="Erreur", border_style="red"))

    # -------------------- settings role prompt --------------------
    def _load_role_prompt(self, role: str) -> None:
        self.query_one("#role_prompt", TextArea).text = self.store.load(f"bmad_roles/{role}.md")

    # -------------------- overrides --------------------
    def _load_overrides(self) -> dict[str, str]:
        p = self.cfg.routing_override_path
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _save_overrides(self) -> None:
        p = self.cfg.routing_override_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._override_by_role, indent=2, ensure_ascii=False), encoding="utf-8")
        self._log_chat("system", f"Overrides sauvegardés: {p}")

    # -------------------- BENCH persistence + reports --------------------
    def _bench_cache_dir(self, program: str) -> Path:
        return self.cfg.cache_root / "bench_runs" / program

    def _bench_state_path(self, program: str) -> Path:
        return self._bench_cache_dir(program) / "bench_state.json"

    def _bench_json_path(self) -> Path:
        return self.cfg.cache_root / "bench.json"

    def _bench_table_jsonl(self, program: str) -> Path:
        return self._bench_cache_dir(program) / "bench_table.jsonl"

    def _reports_dir(self, program: str) -> Path:
        return self.cfg.managed_root / "reports" / program

    def _csv_path(self, program: str, role: str, phase: str) -> Path:
        role = (role or "unknown").strip() or "unknown"
        phase = (phase or "unknown").strip() or "unknown"
        return self._reports_dir(program) / f"{role}.{phase}.csv"

    def _append_csv_row(self, program: str, role: str, phase: str, model: str, score: str, latency_ms: str, status: str) -> None:
        path = self._csv_path(program, role, phase)
        path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not path.exists()
        with path.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["ts", "program", "role", "phase", "model", "score", "latency_ms", "status"])
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), program, role, phase, model, score, latency_ms, status])

    def _bench_fill_billboard_from_bench_json(self) -> None:
        bb = self.query_one("#bb_table", DataTable)
        bb.clear()
        bb.add_columns("role", "best_model", "score", "latency_ms", "override")

        bench_json = _read_json(self._bench_json_path())
        if not bench_json:
            return

        for role, arr in bench_json.items():
            if not isinstance(arr, list) or not arr:
                continue
            best = arr[0] if isinstance(arr[0], dict) else None
            if not best:
                continue
            ov = self._override_by_role.get(str(role), "")
            bb.add_row(
                str(role),
                str(best.get("model", "")),
                str(best.get("format_score", "")),
                str(best.get("latency_ms", "")),
                ov,
            )

    def _bench_persist_bench_json(self) -> None:
        out: dict[str, list[dict[str, Any]]] = {}
        for role, lst in self.router.scores.items():
            rows: list[dict[str, Any]] = []
            for s in lst:
                rows.append(
                    {
                        "model": s.model,
                        "latency_ms": int(s.latency_ms),
                        "format_score": int(s.format_score),
                        "role": s.role,
                        "options": dict(s.options or {}),
                    }
                )
            out[str(role)] = rows
        _write_json(self._bench_json_path(), out)

    def _apply_routing_best(self) -> None:
        if not self.router.scores:
            self._log_chat("system", "Pas de scores en mémoire. Lance/resume un bench.")
            return
        routing: dict[str, Any] = {}
        for role, lst in self.router.scores.items():
            if not lst:
                continue
            best = lst[0]
            routing[str(role)] = {"model": best.model, "options": dict(best.options or {})}
        _write_json(self.cfg.routing_path, routing)
        self._log_chat("system", f"routing.json écrit: {self.cfg.routing_path}")

    def _bench_load_table_history(self) -> None:
        with self._bench_lock:
            program = self._bench.program
        p = self._bench_table_jsonl(program)
        if not p.exists():
            return
        t = self.query_one("#bench_table", DataTable)
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return
        for line in lines[-800:]:
            try:
                obj = json.loads(line)
                if obj.get("type") != "model_done":
                    continue
                t.add_row(
                    str(obj.get("role", "")),
                    str(obj.get("phase", "")),
                    str(obj.get("model", "")),
                    str(obj.get("score", "")),
                    str(obj.get("latency_ms", "")),
                    str(obj.get("status", "")),
                )
            except Exception:
                continue

    def _bench_reload_last_session(self) -> None:
        programs = ["bench-standard", "bench-advanced", "bench-fast"]
        existing = [(p, self._bench_state_path(p)) for p in programs if self._bench_state_path(p).exists()]
        if existing:
            existing.sort(key=lambda x: x[1].stat().st_mtime, reverse=True)
            program = existing[0][0]
        else:
            program = "bench-fast"

        st_path = self._bench_state_path(program)
        state = _read_json(st_path)
        meta = state.get("meta", {}) if isinstance(state.get("meta", {}), dict) else {}
        done = state.get("done", {}) if isinstance(state.get("done", {}), dict) else {}
        updated_at = meta.get("updated_at")

        with self._bench_lock:
            self._bench.program = program
            self._bench.last_state_done = len(done)
            self._bench.last_state_updated_at = float(updated_at) if isinstance(updated_at, (int, float)) else None

        self._bench_fill_billboard_from_bench_json()

    # -------------------- BENCH ticker --------------------
    def _bench_tick_ui(self) -> None:
        with self._bench_lock:
            s = self._bench
            s.ticks_seen += 1

            program = s.program
            running = s.running
            phase = s.phase
            role = s.role
            model = s.model
            last_event = s.last_event

            ticks = s.ticks_seen
            events = s.events_seen
            model_i = s.model_i
            total_models = s.total_models
            step_i = s.step_i
            steps_total = s.steps_total

            last_state_done = s.last_state_done
            last_state_updated_at = s.last_state_updated_at

            rows: list[tuple[str, str, str, str, str, str]] = []
            while s.pending_rows:
                rows.append(s.pending_rows.popleft())

        self.query_one("#bench_program", Static).update(program)
        self.query_one("#bench_running", Static).update("yes" if running else "no")
        self.query_one("#bench_phase", Static).update(phase)
        self.query_one("#bench_role", Static).update(role)
        self.query_one("#bench_model", Static).update(model)
        self.query_one("#bench_event", Static).update(last_event or "—")
        self.query_one("#bench_ticks", Static).update(str(ticks))
        self.query_one("#bench_events", Static).update(str(events))
        self.query_one("#bench_counts", Static).update(f"models {model_i}/{total_models} • steps {step_i}/{steps_total}")

        bar_models = self.query_one("#bench_models_bar", ProgressBar)
        bar_steps = self.query_one("#bench_steps_bar", ProgressBar)
        _pb_set(bar_models, total=total_models, progress=model_i)
        _pb_set(bar_steps, total=steps_total, progress=step_i)

        st_path = self._bench_state_path(program)
        self.query_one("#bench_state_path", Static).update(str(st_path))
        self.query_one("#bench_done", Static).update(str(last_state_done))
        if last_state_updated_at:
            self.query_one("#bench_updated", Static).update(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_state_updated_at)))
        else:
            self.query_one("#bench_updated", Static).update("—")

        if rows:
            t = self.query_one("#bench_table", DataTable)
            for r in rows:
                t.add_row(*r)

    # -------------------- BENCH start --------------------
    def _bench_autostart_a1(self) -> None:
        if self._bench_state_path("bench-standard").exists():
            self._bench_start(program="bench-standard", trials=5, mode="tune", resume=True)
        else:
            self._bench_start(program="bench-fast", trials=1, mode="quick", resume=True)

    def _bench_start(self, *, program: str, trials: int, mode: str, resume: bool) -> None:
        with self._bench_lock:
            if self._bench.running:
                self._log_chat("system", "Bench déjà en cours.")
                return
            self._bench = BenchLiveState(
                running=True,
                program=program,
                phase="(starting)",
                role="—",
                model="—",
                model_i=0,
                total_models=max(1, len(self.models)),
                step_i=0,
                steps_total=1,
                last_event="start",
                stop_requested=False,
            )

        bt = self.query_one("#bench_table", DataTable)
        bt.clear()
        bt.add_columns("role", "phase", "model", "score", "latency_ms", "status")
        self._bench_load_table_history()

        cache_dir = self._bench_cache_dir(program)
        cache_dir.mkdir(parents=True, exist_ok=True)
        state_path = self._bench_state_path(program)

        def progress(evt: str, payload: dict[str, Any]) -> None:
            with self._bench_lock:
                b = self._bench
                b.events_seen += 1
                b.last_event = evt

                if evt == "phase_start":
                    b.phase = str(payload.get("phase", "—"))
                    b.role = "—"
                    b.model = "—"
                    b.model_i = 0
                    b.step_i = 0
                    b.steps_total = 1

                elif evt == "role_start":
                    b.role = str(payload.get("role", "—"))

                elif evt == "model_start":
                    b.role = str(payload.get("role", b.role))
                    b.model = str(payload.get("model", "—"))
                    try:
                        b.model_i = int(payload.get("model_i", b.model_i))
                    except Exception:
                        pass
                    try:
                        b.total_models = int(payload.get("total_models", b.total_models)) or b.total_models
                    except Exception:
                        pass
                    try:
                        b.steps_total = int(payload.get("steps_total", b.steps_total)) or b.steps_total
                    except Exception:
                        pass
                    b.step_i = 0

                elif evt == "step_done":
                    b.step_i = min(b.steps_total, b.step_i + 1)

                elif evt == "model_done":
                    role = str(payload.get("role", ""))
                    phase = str(payload.get("phase", b.phase))
                    model = str(payload.get("model", ""))
                    score = str(payload.get("score", ""))
                    latency_ms = str(payload.get("latency_ms", ""))
                    status = str(payload.get("status", ""))

                    row = (role, phase, model, score, latency_ms, status)
                    b.pending_rows.append(row)

                    # JSONL history (resume UI)
                    try:
                        _write_jsonl(
                            self._bench_table_jsonl(program),
                            {
                                "type": "model_done",
                                "ts": time.time(),
                                "program": program,
                                "role": role,
                                "phase": phase,
                                "model": model,
                                "score": score,
                                "latency_ms": latency_ms,
                                "status": status,
                            },
                        )
                    except Exception:
                        pass

                    # CSV report (old style)
                    try:
                        self._append_csv_row(program, role, phase, model, score, latency_ms, status)
                    except Exception:
                        pass

                # read bench_state.json for done/updated_at
                if state_path.exists():
                    st = _read_json(state_path)
                    done = st.get("done", {}) if isinstance(st.get("done", {}), dict) else {}
                    meta = st.get("meta", {}) if isinstance(st.get("meta", {}), dict) else {}
                    b.last_state_done = len(done)
                    ua = meta.get("updated_at")
                    if isinstance(ua, (int, float)):
                        b.last_state_updated_at = float(ua)

        def worker() -> None:
            try:
                kwargs: dict[str, Any] = dict(
                    roles=None,
                    models=None,
                    max_models=0,
                    trials=trials,
                    mode=mode,
                    cache_dir=cache_dir,
                    resume=resume,
                    program=program,
                    progress=progress,
                )
                sig = inspect.signature(self.router.bench)
                if "should_stop" in sig.parameters:
                    kwargs["should_stop"] = lambda: bool(self._bench.stop_requested)

                self.router.bench(**kwargs)

                self._bench_persist_bench_json()
                self.call_from_thread(self._bench_fill_billboard_from_bench_json)
                self.call_from_thread(self._log_chat, "system", f"Bench terminé: {program} (resume={resume})")
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Bench error: {type(e).__name__}: {e}")
            finally:
                with self._bench_lock:
                    self._bench.running = False

        threading.Thread(target=worker, daemon=True).start()

    # -------------------- save / close --------------------
    def _save_everything_best_effort(self) -> None:
        try:
            self._save_overrides()
        except Exception:
            pass
        try:
            base = self.query_one("#chat_base_prompt", TextArea).text or ""
            self.store.save("chat_base_fr.md", base)
        except Exception:
            pass
        try:
            role = str(self.query_one("#role_select", Select).value or "")
            if role:
                txt = self.query_one("#role_prompt", TextArea).text or ""
                self.store.save(f"bmad_roles/{role}.md", txt)
        except Exception:
            pass
        try:
            if getattr(self.router, "scores", None):
                self._bench_persist_bench_json()
        except Exception:
            pass

    def _save_and_exit(self) -> None:
        with self._bench_lock:
            running = bool(self._bench.running)
            self._bench.stop_requested = True

        self._save_everything_best_effort()

        if not running:
            self.exit()
            return

        self._log_chat("system", "Bench en cours: stop soft demandé. Fermeture dès que possible (timeout 10s).")
        deadline = time.time() + 10.0
        timer_ref: dict[str, Any] = {"timer": None}

        def _poll_exit() -> None:
            with self._bench_lock:
                still = bool(self._bench.running)
            if (not still) or time.time() >= deadline:
                t = timer_ref.get("timer")
                if t is not None:
                    try:
                        t.stop()
                    except Exception:
                        pass
                self.exit()

        timer_ref["timer"] = self.set_interval(0.25, _poll_exit)

    # -------------------- BMAD run --------------------
    async def _bmad_prompt_and_run(self) -> None:
        goal = await self.push_screen_wait(GoalPrompt())
        if not goal:
            return

        self._log_bmad(f"### Goal\n\n{goal}", title="BMAD Goal")
        self._log_bmad("Lancement Orchestrator.run_bmad_cycle(...) en background…", title="BMAD")

        def worker() -> None:
            try:
                logger = logging.getLogger("freya")
                orch = Orchestrator(self.cfg, logger)
                out = orch.run_bmad_cycle(goal)
                lines = ["### Terminé", "", "Artefacts:"]
                for p in out:
                    lines.append(f"- `{p}`")
                self.call_from_thread(self._log_bmad, "\n".join(lines), "BMAD")
            except Exception as e:
                self.call_from_thread(self._log_bmad, f"Erreur: {type(e).__name__}: {e}", "BMAD ERROR")
            finally:
                self.call_from_thread(self._ensure_output_root)
                self.call_from_thread(self._refresh_tree)

        threading.Thread(target=worker, daemon=True).start()

    # -------------------- buttons --------------------
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        # bench
        if bid == "btn_bench_fast":
            self._bench_start(program="bench-fast", trials=1, mode="quick", resume=True)
            return
        if bid == "btn_bench_resume_std":
            self._bench_start(program="bench-standard", trials=5, mode="tune", resume=True)
            return
        if bid == "btn_bench_standard":
            self._bench_start(program="bench-standard", trials=5, mode="tune", resume=True)
            return
        if bid == "btn_bench_advanced":
            self._bench_start(program="bench-advanced", trials=5, mode="tune", resume=True)
            return
        if bid == "btn_bench_stop":
            with self._bench_lock:
                self._bench.stop_requested = True
            self._log_chat("system", "Stop soft demandé (si supporté par router).")
            return
        if bid == "btn_apply_routing":
            self._apply_routing_best()
            return
        if bid == "btn_reload_state":
            self._bench_reload_last_session()
            bt = self.query_one("#bench_table", DataTable)
            bt.clear()
            bt.add_columns("role", "phase", "model", "score", "latency_ms", "status")
            self._bench_load_table_history()
            self._log_chat("system", "Session bench rechargée (state + table + billboard).")
            return
        if bid == "btn_save_and_exit":
            self._save_and_exit()
            return

        # bmad
        if bid == "btn_bmad_run":
            self.call_after_refresh(lambda: asyncio.create_task(self._bmad_prompt_and_run()))
            return

        # others (chat/settings)
        if bid == "btn_send":
            self.action_send_chat()
        elif bid == "btn_clear":
            self.query_one("#chat_input", TextArea).text = ""
        elif bid == "btn_copy":
            self.action_copy_last()
        elif bid == "btn_watch":
            self._cyber_watch()
        elif bid == "btn_search":
            self._log_chat("system", "Utilise: /search <requête> (gratuit via Wikipedia).")
        elif bid == "btn_apply_override":
            role = str(self.query_one("#ov_role", Select).value or "")
            model = str(self.query_one("#ov_model", Select).value or "")
            if role and model:
                self._override_by_role[role] = model
                self._log_chat("system", f"Override: {role} -> {model}")
        elif bid == "btn_save_overrides":
            self._save_overrides()
        elif bid == "btn_set_out":
            self._set_output_dir()
        elif bid == "btn_open_vscode":
            self._run_ps(f'code "{self.output_root}"')
        elif bid == "btn_refresh_artifacts":
            self._ensure_output_root()
            self._refresh_tree()
        elif bid == "btn_load_role":
            role = str(self.query_one("#role_select", Select).value or "analyst")
            self._load_role_prompt(role)
        elif bid == "btn_save_role":
            role = str(self.query_one("#role_select", Select).value or "analyst")
            self.store.save(f"bmad_roles/{role}.md", self.query_one("#role_prompt", TextArea).text or "")
            self._log_chat("system", f"Prompt sauvegardé: bmad_roles/{role}.md")

    # -------------------- chat actions --------------------
    def action_send_chat(self) -> None:
        text = (self.query_one("#chat_input", TextArea).text or "").strip()
        if not text:
            return
        self.query_one("#chat_input", TextArea).text = ""
        self._log_chat("user", text)

        if text.startswith("/search "):
            self._search(text[len("/search ") :].strip())
            return

        self._chat_generate(text)

    def action_copy_last(self) -> None:
        if not self.last_assistant:
            self._log_chat("system", "Rien à copier.")
            return
        try:
            copy_clipboard_windows(self.last_assistant)
            self._log_chat("system", "Dernière réponse copiée.")
        except Exception as e:
            self._log_chat("system", f"Copie KO: {type(e).__name__}: {e}")

    def _search(self, query: str) -> None:
        self._set_thinking(True)

        def worker() -> None:
            try:
                items = wiki_search(query, limit=5)
                if not items:
                    self.call_from_thread(self._log_chat, "tool", f"Aucun résultat pour **{query}**.")
                    return
                lines = [f"### Search (gratuit) — Wikipedia — **{query}**"]
                for it in items:
                    lines.append(f"- [{it['title']}]({it['url']})\n  - {it['snippet']}")
                self.call_from_thread(self._log_chat, "tool", "\n".join(lines))
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Search error: {type(e).__name__}: {e}")
            finally:
                self.call_from_thread(self._set_thinking, False)

        threading.Thread(target=worker, daemon=True).start()

    def _cyber_watch(self) -> None:
        self._set_thinking(True)
        self._log_chat("system", "Cyber Watch: CISA KEV…")

        def worker() -> None:
            try:
                kev = fetch_json("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
                vulns = (kev.get("vulnerabilities") or [])[:10]
                lines = ["### CISA KEV (Top 10)", "URL: https://www.cisa.gov/known-exploited-vulnerabilities-catalog", ""]
                for v in vulns:
                    lines.append(f"- **{v.get('cveID','')}** — {v.get('vendorProject','')} {v.get('product','')}")
                self.call_from_thread(self._log_chat, "tool", "\n".join(lines))
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Cyber Watch error: {type(e).__name__}: {e}")
            finally:
                self.call_from_thread(self._set_thinking, False)

        threading.Thread(target=worker, daemon=True).start()

    def _chat_generate(self, user_text: str) -> None:
        self._set_thinking(True)

        def worker() -> None:
            try:
                base = self.query_one("#chat_base_prompt", TextArea).text or ""
                hat = str(self.query_one("#hat_select", Select).value or "")
                hat_txt = self._get_hat_text(hat)
                today = dt.date.today().isoformat()
                system = f"{base}\n\nDate: {today}\nPreset: {hat}\n{hat_txt}\n"

                primary = str(self.query_one("#primary_model", Select).value or self.models[0])
                r1 = self.client.generate(
                    model=primary,
                    prompt=user_text,
                    system=system,
                    options_extra={"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.05, "num_predict": 900},
                )
                self.call_from_thread(self._log_chat, "assistant", (r1.response or "").strip())
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Chat error: {type(e).__name__}: {e}")
            finally:
                self.call_from_thread(self._set_thinking, False)

        threading.Thread(target=worker, daemon=True).start()

    # -------------------- misc --------------------
    def _set_output_dir(self) -> None:
        val = str(self.query_one("#out_dir", Input).value or "").strip()
        if not val:
            self._log_chat("system", "Output vide.")
            return
        p = Path(val)
        p.mkdir(parents=True, exist_ok=True)
        self.output_root = p
        self._ensure_output_root()
        self._refresh_tree()
        self._log_chat("system", f"Output changé: {self.output_root}")

    def _run_ps(self, cmd: str) -> None:
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], timeout=120)
        except Exception:
            pass


if __name__ == "__main__":
    FreyaTUI().run()

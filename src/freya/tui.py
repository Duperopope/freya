# src/freya/tui.py
from __future__ import annotations

import asyncio
import datetime as dt
import inspect
import json
import os
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Coroutine, cast

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


# -------------------- FREE WEB HELPERS --------------------
def fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Freya/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def wiki_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    # Wikipedia OpenSearch (free)
    # https://www.mediawiki.org/wiki/API:Main_page
    params = urllib.parse.urlencode(
        {"action": "opensearch", "search": query, "limit": str(max(1, min(limit, 10))), "namespace": "0", "format": "json"}
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
        out.append({"title": str(titles[i]), "snippet": str(descs[i]) if i < len(descs) else "", "url": str(links[i]) if i < len(links) else ""})
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
    # https://learn.microsoft.com/powershell/module/microsoft.powershell.management/set-clipboard
    import subprocess
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


# -------------------- EDITABLE PROMPTS STORE (NO EXTRA MODULE) --------------------
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


# -------------------- MODAL GOAL --------------------
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


# -------------------- APP --------------------
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
        self.thinking = False

        self.output_root: Path = self.cfg.output_root

        self._bench_running = False
        self._override_by_role: dict[str, str] = self._load_overrides()

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
                        yield self._bench_toolbar()
                        yield DataTable(id="bench_table")
                        yield self._billboard()

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

    # -------- UI blocks --------
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

    def _bench_toolbar(self) -> Container:
        return Container(
            Horizontal(
                Button(f"{I_PLAY} Bench standard", id="btn_bench_start", variant="primary"),
                Button(f"{I_STOP} Stop (soft)", id="btn_bench_stop"),
                Static("Phase: —", id="bench_phase"),
                Static("Role:", classes="muted"),
                ProgressBar(total=100, id="bench_role_bar"),
                Static("Model:", classes="muted"),
                ProgressBar(total=100, id="bench_model_bar"),
                id="bench_row1",
            ),
            Static("Bench live + billboard. Override possible par rôle.", classes="muted"),
            id="bench_toolbar",
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

    def _bmad_toolbar(self) -> Container:
        return Container(
            Static(
                "BMAD Studio (user friendly)\n"
                "1) Choisis un dossier de sortie\n"
                "2) Donne un objectif\n"
                "3) Freya tente de produire artefacts + code\n",
                id="bmad_overview",
            ),
            Horizontal(
                Static("Output:", classes="muted"),
                Input(value=str(self.output_root), id="out_dir"),
                Button("Set", id="btn_set_out", variant="primary"),
                Button(f"{I_OPEN} VS Code", id="btn_open_vscode"),
                Button("Sync BMAD", id="btn_sync_bmad"),
                Button("Run BMAD (goal)", id="btn_run_bmad", variant="primary"),
                Button("Refresh artefacts", id="btn_refresh_artifacts"),
                id="bmad_actions",
            ),
            id="bmad_toolbar",
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
            Static("Notes", id="set_notes"),
            Static(
                "Web search: gratuit via Wikipedia API (/search ...).\n"
                "Icônes: activer une Nerd Font dans Windows Terminal.",
                classes="muted",
            ),
            id="settings_panel",
        )

    # -------- lifecycle --------
    def on_mount(self) -> None:
        # load models
        try:
            self.models = self.router.list_models()
        except Exception:
            self.models = []
        if not self.models:
            self.models = ["llama3.1:8b"]

        self.query_one("#primary_model", Select).set_options([(m, m) for m in self.models])
        self.query_one("#summarizer_model", Select).set_options([(m, m) for m in self.models])
        self.query_one("#ov_model", Select).set_options([(m, m) for m in self.models])

        self.query_one("#primary_model", Select).value = self._prefer(["llama3.1:8b", "mistral:7b", "qwen3:8b"])
        self.query_one("#summarizer_model", Select).value = self._prefer(["llama3.1:8b", "qwen2.5-coder:7b", "mistral:7b"])

        # hats from file
        hats = self._hat_options()
        self.query_one("#hat_select", Select).set_options(hats)
        self.query_one("#hat_select", Select).value = hats[0][0]

        # chat base prompt editable
        cb = self.query_one("#chat_base_prompt", TextArea)
        cb.border_title = "Chat base FR — éditable (.freya/config/prompts/chat_base_fr.md)"
        cb.text = self.store.load("chat_base_fr.md")

        ci = self.query_one("#chat_input", TextArea)
        ci.border_title = "Message (Ctrl+Enter envoyer) • /search <requête>"
        ci.text = ""

        # settings role prompt
        rp = self.query_one("#role_prompt", TextArea)
        rp.border_title = "Prompt BMAD role — éditable (.freya/config/prompts/bmad_roles/<role>.md)"
        self._load_role_prompt("analyst")

        # tables
        bt = self.query_one("#bench_table", DataTable)
        bt.add_columns("role", "phase", "model", "score", "latency_ms", "status")

        bb = self.query_one("#bb_table", DataTable)
        bb.add_columns("role", "best_model", "score", "latency_ms", "override")

        # artifacts
        self._ensure_output_root()
        self._refresh_tree()

        self._log_chat("system", "Prêt. Chat FR. Cyber Watch gratuit. /search gratuit (Wikipedia).")

    def _prefer(self, candidates: list[str]) -> str:
        for c in candidates:
            if c in self.models:
                return c
        return self.models[0]

    # -------- hats parsing --------
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

    # -------- logging + thinking --------
    def _set_thinking(self, on: bool) -> None:
        w = self.query_one("#thinking", Static)
        if on:
            w.remove_class("hidden")
        else:
            w.add_class("hidden")

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

    # -------- artifacts tree (no recreate) --------
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
                        except Exception as e:
                            # logging robuste (Textual a self.log)
                            try:
                                self.log.error("Artifacts tree reload failed: %r", e)
                            except Exception:
                                pass

                    # Après le refresh UI, on schedule une VRAIE coroutine (_runner())
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

    # -------- settings (role prompts) --------
    def _load_role_prompt(self, role: str) -> None:
        self.query_one("#role_prompt", TextArea).text = self.store.load(f"bmad_roles/{role}.md")

    def _save_role_prompt(self, role: str) -> None:
        self.store.save(f"bmad_roles/{role}.md", self.query_one("#role_prompt", TextArea).text or "")
        self._log_chat("system", f"Prompt sauvegardé: bmad_roles/{role}.md")

    # -------- overrides --------
    def _load_overrides(self) -> dict[str, str]:
        p = self.cfg.routing_override_path
        try:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_overrides(self) -> None:
        p = self.cfg.routing_override_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._override_by_role, indent=2), encoding="utf-8")
        self._log_chat("system", f"Overrides sauvegardés: {p}")

    # -------- button events --------
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

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
        elif bid == "btn_bench_start":
            self._bench_start()
        elif bid == "btn_bench_stop":
            self._bench_running = False
            self._log_chat("system", "Stop soft demandé.")
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
        elif bid == "btn_sync_bmad":
            self._run_ps("freya sync-bmad")
        elif bid == "btn_run_bmad":
            self._prompt_and_run_bmad()
        elif bid == "btn_refresh_artifacts":
            self._ensure_output_root()
            self._refresh_tree()
        elif bid == "btn_load_role":
            role = str(self.query_one("#role_select", Select).value or "analyst")
            self._load_role_prompt(role)
        elif bid == "btn_save_role":
            role = str(self.query_one("#role_select", Select).value or "analyst")
            self._save_role_prompt(role)

    # -------- actions --------
    def action_send_chat(self) -> None:
        text = (self.query_one("#chat_input", TextArea).text or "").strip()
        if not text:
            return
        self.query_one("#chat_input", TextArea).text = ""
        self._log_chat("user", text)

        if text.startswith("/search "):
            q = text[len("/search "):].strip()
            self._search(q)
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

    # -------- free search --------
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

    # -------- free cyber watch --------
    def _cyber_watch(self) -> None:
        self._set_thinking(True)
        self._log_chat("system", "Cyber Watch: CISA KEV (gratuit)…")

        def worker() -> None:
            try:
                kev = fetch_json("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
                vulns = (kev.get("vulnerabilities") or [])[:10]
                lines = ["### CISA KEV (Top 10) — source officielle", "URL: https://www.cisa.gov/known-exploited-vulnerabilities-catalog", ""]
                for v in vulns:
                    cve = v.get("cveID", "")
                    vendor = v.get("vendorProject", "")
                    product = v.get("product", "")
                    added = v.get("dateAdded", "")
                    due = v.get("dueDate", "")
                    lines.append(f"- **{cve}** — {vendor} {product} (added {added}, due {due})")
                payload = "\n".join(lines)
                self.call_from_thread(self._log_chat, "tool", payload)
                self.call_from_thread(self._chat_generate, "Résume ces KEV en FR (défensif): priorités + actions patch/mitigation/détection.")
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Cyber Watch error: {type(e).__name__}: {e}")
            finally:
                self.call_from_thread(self._set_thinking, False)

        threading.Thread(target=worker, daemon=True).start()

    # -------- chat generate --------
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
                summarizer = str(self.query_one("#summarizer_model", Select).value or primary)
                auto = bool(self.query_one("#best_models", Checkbox).value)

                primary_use = primary
                if auto and "dolphin-llama3:8b" in self.models:
                    primary_use = "dolphin-llama3:8b"

                r1 = self.client.generate(
                    model=primary_use,
                    prompt=user_text,
                    system=system,
                    options_extra={"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.05, "num_predict": 900},
                )
                answer = (r1.response or "").strip()

                r2 = self.client.generate(
                    model=summarizer,
                    prompt=("Résume et structure en FR:\n- TL;DR\n- Actions\n- Risques\n- Next steps\n\n" + answer),
                    system="Tu es un summarizer FR. Concis et structuré.",
                    options_extra={"temperature": 0.0, "top_p": 1.0, "repeat_penalty": 1.05, "num_predict": 450},
                )
                summary = (r2.response or "").strip()
                self.call_from_thread(self._log_chat, "assistant", f"{answer}\n\n---\n## Résumé\n{summary}\n\n*(primary={primary_use}, summarizer={summarizer})*")
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Chat error: {type(e).__name__}: {e}")
            finally:
                self.call_from_thread(self._set_thinking, False)

        threading.Thread(target=worker, daemon=True).start()

    # -------- bench + billboard --------
    def _bench_start(self) -> None:
        if self._bench_running:
            self._log_chat("system", "Bench déjà en cours.")
            return
        self._bench_running = True

        bt = self.query_one("#bench_table", DataTable)
        bt.clear()

        bb = self.query_one("#bb_table", DataTable)
        bb.clear()
        bb.add_columns("role", "best_model", "score", "latency_ms", "override")

        phase_lbl = self.query_one("#bench_phase", Static)
        role_bar = self.query_one("#bench_role_bar", ProgressBar)
        model_bar = self.query_one("#bench_model_bar", ProgressBar)
        role_bar.update(total=100, progress=0)
        model_bar.update(total=100, progress=0)

        def progress(evt: str, payload: dict[str, Any]) -> None:
            if not self._bench_running:
                return
            if evt == "phase_start":
                self.call_from_thread(phase_lbl.update, f"Phase: {payload.get('phase')}")
                self.call_from_thread(role_bar.update, total=100, progress=0)
                self.call_from_thread(model_bar.update, total=100, progress=0)
            elif evt == "model_start":
                i = int(payload.get("model_i", 0))
                n = int(payload.get("total_models", 1)) or 1
                self.call_from_thread(role_bar.update, total=100, progress=int((i / n) * 100))
            elif evt == "model_done":
                row = (
                    str(payload.get("role", "")),
                    str(payload.get("phase", "")),
                    str(payload.get("model", "")),
                    str(payload.get("score", "")),
                    str(payload.get("latency_ms", "")),
                    str(payload.get("status", "")),
                )
                self.call_from_thread(bt.add_row, *row)

        def worker() -> None:
            try:
                cache_dir = self.cfg.cache_root / "bench_runs" / "bench-standard"
                cache_dir.mkdir(parents=True, exist_ok=True)
                scores = self.router.bench(
                    roles=None,
                    models=None,
                    max_models=0,
                    trials=5,
                    mode="tune",
                    cache_dir=cache_dir,
                    resume=True,
                    program="bench-standard",
                    progress=progress,
                )

                # billboard best per role
                def fill_billboard() -> None:
                    for role, lst in scores.items():
                        if not lst:
                            continue
                        best = lst[0]
                        ov = self._override_by_role.get(role, "")
                        bb.add_row(role, best.model, str(best.format_score), str(best.latency_ms), ov)

                self.call_from_thread(fill_billboard)
                self.call_from_thread(self._log_chat, "system", "Bench terminé (billboard mis à jour).")
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Bench error: {type(e).__name__}: {e}")
            finally:
                self._bench_running = False

        threading.Thread(target=worker, daemon=True).start()

    # -------- BMAD output + run --------
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

    def _prompt_and_run_bmad(self) -> None:
        def after(goal: str | None) -> None:
            if not goal:
                self._log_chat("system", "BMAD annulé.")
                return
            safe = goal.replace("`", "``").replace('"', '""')
            env = os.environ.copy()
            env["FREYA_OUTPUT_ROOT"] = str(self.output_root)

            def run() -> None:
                try:
                    self.call_from_thread(self._log_chat, "tool", f"BMAD goal: **{goal}**\nOutput: `{self.output_root}`")
                    subprocess.run(["powershell", "-NoProfile", "-Command", f'freya run --goal "{safe}"'], env=env, timeout=60 * 60)
                    self.call_from_thread(self._log_chat, "system", "BMAD terminé. Refresh artefacts.")
                    self.call_from_thread(self._refresh_tree)
                except Exception as e:
                    self.call_from_thread(self._log_chat, "system", f"BMAD error: {type(e).__name__}: {e}")

            threading.Thread(target=run, daemon=True).start()

        self.push_screen(GoalPrompt(), after)

    def _run_ps(self, cmd: str) -> None:
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], timeout=120)
        except Exception:
            pass

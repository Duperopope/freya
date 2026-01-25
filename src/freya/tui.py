# src/freya/tui.py
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    Static,
    Button,
    Input,
    RichLog,
    DataTable,
    Select,
    Checkbox,
    TextArea,
    ProgressBar,
)

from rich.markdown import Markdown
from rich.panel import Panel

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter
from .tools.webwatch import cyber_watch
from .tools.shell import run_powershell
from .tools.clipboard import copy_to_clipboard_windows
from .tools.redact import redact_secrets


# Nerd Font icons (best effort). If you don't see them: set Nerd Font in Windows Terminal.
I_CHAT = "󰭹"
I_BENCH = "󱎴"
I_DEV = "󰨞"
I_SET = "󰒓"
I_FILE = "󰈙"
I_WATCH = "󰔚"
I_COPY = "󰆏"
I_PLAY = "󰐊"
I_STOP = "󰓛"
I_OPEN = "󰏌"


@dataclass
class ChatMsg:
    role: str
    content: str


PRESETS: dict[str, str] = {
    "Blue Hat (défense)": (
        "Assistant cybersécurité DEFENSIF (blue team). Durcissement, patching, audit, SOC, IR. "
        "Refuse toute demande illégale/offensive et propose alternatives défensives."
    ),
    "White Hat (pentest légal)": (
        "Assistant pentest légal et cadré. Méthodo, outillage légal, reporting, remédiation. "
        "Évite les détails directement exploitables."
    ),
    "Grey Hat (research)": (
        "Veille et research: CVE, risques, mitigations, PoC high-level. "
        "Pas d'instructions d'exploitation. Priorité défense."
    ),
    "Red Team (simulation autorisée)": (
        "Simulation autorisée: threat modeling, MITRE ATT&CK TTPs, détection, évaluation. "
        "Refuse toute aide illégale/offensive réelle."
    ),
}


def _safe_id(text: str) -> str:
    bad = '<>:"/\\|?*'
    s = text
    for ch in bad:
        s = s.replace(ch, "_")
    s = s.replace(" ", "_")
    return s[:120] if len(s) > 120 else s


class FreyaTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #main { height: 1fr; }
    #left { width: 60%; }
    #right { width: 40%; border-left: solid gray; padding: 1; }

    #chat_controls { height: auto; }
    #chat_log { height: 1fr; }
    #chat_in { height: auto; }

    #bench_controls { height: auto; }
    #bench_table { height: 1fr; }

    #artifact_list { height: 18; }
    #artifact_status { height: 3; color: $text-muted; }
    """

    BINDINGS = [
        ("ctrl+w", "cyber_watch", "Cyber Watch"),
        ("ctrl+c", "copy_last_answer", "Copy last answer"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.cfg = FreyaConfig.load()
        self.client = OllamaClient(base_url=self.cfg.ollama.base_url)
        self.router = LLMRouter(self.client)

        self.models: list[str] = []
        self.output_root: Path = self.cfg.artifacts_root
        self.selected_artifact: Path | None = None
        self._last_hover_id: str | None = None

        self._last_assistant_raw: str = ""
        self._bench_running = False

    # ---------- UI ----------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main"):
            with Vertical(id="left"):
                with TabbedContent():
                    # CHAT TAB
                    with TabPane(f"{I_CHAT} Chat", id="tab_chat"):
                        with Horizontal(id="chat_controls"):
                            yield Static("Preset:")
                            yield Select([(k, k) for k in PRESETS.keys()], id="preset_select")
                            yield Static("Primary:")
                            yield Select([], id="primary_model")
                            yield Static("Summarizer:")
                            yield Select([], id="summarizer_model")
                            yield Checkbox("Best models (auto)", id="best_models")
                            yield Button(f"{I_WATCH} Cyber Watch", id="btn_watch", variant="primary")
                            yield Button(f"{I_COPY} Copier dernière réponse", id="btn_copy")
                            yield Button("PowerShell (approved)", id="btn_shell")

                        instr = TextArea(id="custom_instructions")
                        instr.border_title = "Instructions personnalisées (tu peux tout personnaliser)"
                        yield instr

                        yield RichLog(id="chat_log", wrap=True)
                        yield Input(placeholder="Message… (/watch) — Ctrl+W: Cyber Watch — Ctrl+C: Copier", id="chat_in")

                    # BENCH TAB
                    with TabPane(f"{I_BENCH} Benchmark", id="tab_bench"):
                        with Horizontal(id="bench_controls"):
                            yield Button(f"{I_PLAY} Start bench-standard", id="btn_bench_start", variant="primary")
                            yield Button(f"{I_STOP} Stop (soft)", id="btn_bench_stop")
                            yield Static("Phase:", id="bench_phase")
                            yield ProgressBar(total=100, id="bench_role_bar")
                            yield ProgressBar(total=100, id="bench_model_bar")

                        bt = DataTable(id="bench_table")
                        yield bt

                    # WEBDEV TAB
                    with TabPane(f"{I_DEV} Webdeveloper (BMAD)", id="tab_webdev"):
                        yield Static(
                            "Logique BMAD (artefact-first):\n"
                            "Phase 1 Planning: Analyst→project-brief.md → PM→PRD.md → Architect→architecture.md → PO→epic-*.md\n"
                            "Phase 2 Dev: SM→*.story.md → DEV→code/tests → QA→QA.md + traceability\n",
                            id="bmad_logic",
                        )
                        with Horizontal():
                            yield Button("Ouvrir VS Code (workspace)", id="btn_open_vscode")
                            yield Button("Rafraîchir artefacts", id="btn_refresh_artifacts")
                        yield RichLog(id="webdev_log", wrap=True)
                        yield Input(placeholder="Demande projet (langage naturel)…", id="webdev_in")

                    # SETTINGS TAB
                    with TabPane(f"{I_SET} Settings", id="tab_settings"):
                        yield Static(
                            "Settings:\n"
                            "- Fonts / taille = Windows Terminal\n"
                            "- Output root = .freya/artifacts (modifiable bientôt)\n"
                            "- Logs: .freya/logs/\n",
                            id="settings_txt",
                        )

            # RIGHT PANE (always)
            with Vertical(id="right"):
                yield Static("BMAD artefacts / overview", id="right_title")
                yield Static(f"Output root: {self.output_root}", id="out_root")
                yield ScrollableContainer(id="artifact_list")
                yield Static("Hover: —\nSelected: —", id="artifact_status")

        yield Footer()

    def on_mount(self) -> None:
        # models
        try:
            self.models = self.router.list_models()
        except Exception:
            self.models = []
        if not self.models:
            self.models = ["llama3.1:8b"]

        # fill selects
        self.query_one("#preset_select", Select).value = "Blue Hat (défense)"
        primary = self.query_one("#primary_model", Select)
        summarizer = self.query_one("#summarizer_model", Select)
        primary.set_options([(m, m) for m in self.models])
        summarizer.set_options([(m, m) for m in self.models])
        primary.value = self._prefer_model(["llama3.1:8b", "mistral:7b", "qwen3:8b"])
        summarizer.value = self._prefer_model(["llama3.1:8b", "qwen2.5-coder:7b", "mistral:7b"])

        # bench table
        bt = self.query_one("#bench_table", DataTable)
        bt.add_columns("role", "phase", "model", "score", "latency_ms", "status")
        bt.cursor_type = "row"

        self._refresh_artifacts()
        self._chat_log_system("Freya UI prête. /watch pour l'actu cyber (sources officielles).")

    # ---------- Hover artifacts (mouse move) ----------
    def on_mouse_move(self, event: events.MouseMove) -> None:
        try:
            widget, _ = self.screen.get_widget_at(event.screen_x, event.screen_y)
        except Exception:
            return
        if not isinstance(widget, Button):
            return
        wid = widget.id or ""
        if not wid.startswith("art_") or wid == self._last_hover_id:
            return
        self._last_hover_id = wid
        p_str = getattr(widget, "freya_path", "")
        if p_str:
            self._set_artifact_status(hover=Path(p_str).name)

    # ---------- Chat logging ----------
    def _chat_log_system(self, text: str) -> None:
        self._chat_log("system", text)

    def _chat_log(self, role: str, text: str) -> None:
        log = self.query_one("#chat_log", RichLog)
        text = redact_secrets(text)

        if role == "assistant":
            # Pretty render: Markdown in a Panel
            renderable = Panel(Markdown(text), title="Assistant", border_style="cyan")
            log.write(renderable)
            self._last_assistant_raw = text
        elif role == "user":
            renderable = Panel(Markdown(text), title="Vous", border_style="green")
            log.write(renderable)
        elif role == "tool":
            renderable = Panel(Markdown(text), title="Tool", border_style="magenta")
            log.write(renderable)
        else:
            log.write(f"[{role}] {text}")

    # ---------- Helpers ----------
    def _prefer_model(self, candidates: list[str]) -> str:
        for c in candidates:
            if c in self.models:
                return c
        return self.models[0]

    def _system_prompt(self) -> str:
        import datetime as dt

        today = dt.date.today().isoformat()
        preset_name = str(self.query_one("#preset_select", Select).value or "Blue Hat (défense)")
        preset_txt = PRESETS.get(preset_name, PRESETS["Blue Hat (défense)"])
        custom = self.query_one("#custom_instructions", TextArea).text or ""

        return (
            "Tu es Freya. Tu réponds en français.\n"
            f"Date: {today}\n"
            f"Orientation: {preset_name}\n"
            f"{preset_txt}\n"
            "Règles: pas d'illégal, pas d'instructions d'attaque. Alternatives défensives uniquement.\n\n"
            "Instructions personnalisées:\n"
            f"{custom}\n"
        )

    # ---------- Artifact list ----------
    def _artifact_candidates(self) -> list[Path]:
        root = self.output_root
        if not root.exists():
            return []
        files = list(root.rglob("*.md"))

        def rank(p: Path) -> tuple[int, str]:
            name = p.name.lower()
            pri = 9
            if name == "project-brief.md":
                pri = 0
            elif name == "prd.md":
                pri = 1
            elif name == "architecture.md":
                pri = 2
            elif name.startswith("epic-"):
                pri = 3
            elif name.endswith(".story.md"):
                pri = 4
            return (pri, str(p).lower())

        files.sort(key=rank)
        return files[:120]

    def _refresh_artifacts(self) -> None:
        container = self.query_one("#artifact_list", ScrollableContainer)
        container.remove_children()

        files = self._artifact_candidates()
        if not files:
            container.mount(Static("Aucun artefact trouvé (encore). Lance un run BMAD pour générer."))
            return

        for p in files:
            b = Button(f"{I_FILE} {p.name}", id=f"art_{_safe_id(str(p))}")
            setattr(b, "freya_path", str(p))
            container.mount(b)

    def _set_artifact_status(self, hover: str | None = None, selected: str | None = None) -> None:
        st = self.query_one("#artifact_status", Static)
        hover_s = hover or "—"
        sel = selected or (str(self.selected_artifact) if self.selected_artifact else "—")
        st.update(f"Hover: {hover_s}\nSelected: {sel}")

    # ---------- Buttons / inputs ----------
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid == "btn_watch":
            self.do_cyber_watch()
            return
        if bid == "btn_copy":
            self.action_copy_last_answer()
            return
        if bid == "btn_shell":
            self.do_shell_status()
            return
        if bid == "btn_bench_start":
            self.do_bench_start()
            return
        if bid == "btn_bench_stop":
            self._chat_log_system("Stop soft: laisse finir la requête en cours (backend LLM).")
            self._bench_running = False
            return
        if bid == "btn_open_vscode":
            self.do_open_vscode_workspace()
            return
        if bid == "btn_refresh_artifacts":
            self._refresh_artifacts()
            return

        if bid.startswith("art_"):
            p_str = getattr(event.button, "freya_path", "")
            p = Path(p_str)
            if p.exists():
                self.selected_artifact = p
                self._set_artifact_status(selected=str(p))
                self.do_open_in_vscode(p)
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return

        if event.input.id == "chat_in":
            if text == "/watch":
                self.do_cyber_watch()
                return
            self._chat_log("user", text)
            self.do_chat_generate(text)
            return

        if event.input.id == "webdev_in":
            self._chat_log("tool", f"Webdev request: {text}")
            self._chat_log("assistant", "OK. Prochaine étape: boutons BMAD (générer brief/PRD/architecture/epics/stories).")
            return

    # ---------- Actions ----------
    def action_cyber_watch(self) -> None:
        self.do_cyber_watch()

    def action_copy_last_answer(self) -> None:
        if not self._last_assistant_raw:
            self._chat_log_system("Rien à copier pour l’instant.")
            return
        try:
            copy_to_clipboard_windows(self._last_assistant_raw)
            self._chat_log_system("Dernière réponse copiée dans le presse-papiers.")
        except Exception as e:
            self._chat_log_system(f"Erreur copie clipboard: {type(e).__name__}: {e}")

    def do_open_in_vscode(self, path: Path) -> None:
        try:
            run_powershell(
                cmd=f'code -g "{path}"',
                audit_log=self.cfg.logs_root / "audit_shell.jsonl",
                timeout_sec=10,
                approved=True,
            )
        except Exception as e:
            self._chat_log_system(f"VS Code open error: {type(e).__name__}: {e}")

    def do_open_vscode_workspace(self) -> None:
        # open workspace root
        try:
            run_powershell(
                cmd=f'code "{Path.cwd()}"',
                audit_log=self.cfg.logs_root / "audit_shell.jsonl",
                timeout_sec=10,
                approved=True,
            )
        except Exception as e:
            self._chat_log_system(f"VS Code open error: {type(e).__name__}: {e}")

    def do_shell_status(self) -> None:
        cmd = "freya status"
        try:
            res = run_powershell(
                cmd=cmd,
                audit_log=self.cfg.logs_root / "audit_shell.jsonl",
                timeout_sec=20,
                approved=True,
            )
            out = (res.stdout or res.stderr).strip()
            self._chat_log("tool", f"```powershell\nPS> {cmd}\n{out}\n```")
        except Exception as e:
            self._chat_log_system(f"PowerShell tool error: {type(e).__name__}: {e}")

    def do_cyber_watch(self) -> None:
        self._chat_log_system("Cyber Watch: récupération (CISA KEV + CERT-FR)…")

        def worker() -> None:
            try:
                items = cyber_watch(self.cfg.cache_root / "web")
                lines = []
                for it in items[:12]:
                    lines.append(f"- **[{it.source}]** {it.title}\n  - Date: {it.published}\n  - URL: {it.url}")
                payload = "\n".join(lines)

                self.call_from_thread(self._chat_log, "tool", payload)

                prompt = (
                    "Résume en FR (mode défensif) :\n"
                    "1) Top 5 items les plus critiques\n"
                    "2) Actions immédiates (patch/mitigation/détection)\n"
                    "3) Priorisation (KEV d'abord)\n"
                    "4) Points de contrôle (logs/EDR/WAF)\n\n"
                    f"{payload}"
                )
                self.call_from_thread(self.do_chat_generate, prompt)
            except Exception as e:
                self.call_from_thread(self._chat_log_system, f"Cyber Watch error: {type(e).__name__}: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def do_chat_generate(self, user_text: str) -> None:
        def worker() -> None:
            try:
                system = self._system_prompt()
                primary = str(self.query_one("#primary_model", Select).value or self.models[0])
                summarizer = str(self.query_one("#summarizer_model", Select).value or primary)
                best_mode = bool(self.query_one("#best_models", Checkbox).value)

                primary_use = primary
                if best_mode and "dolphin-llama3:8b" in self.models:
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
                    prompt=(
                        "Résume et structure en FR:\n"
                        "- TL;DR\n"
                        "- Actions\n"
                        "- Risques\n"
                        "- Next steps\n\n"
                        f"{answer}"
                    ),
                    system="Tu es un summarizer FR. Très concis et structuré.",
                    options_extra={"temperature": 0.0, "top_p": 1.0, "repeat_penalty": 1.05, "num_predict": 450},
                )
                summary = (r2.response or "").strip()
                self.call_from_thread(self._chat_log, "assistant", f"{answer}\n\n---\n## Résumé\n{summary}")
            except Exception as e:
                self.call_from_thread(self._chat_log_system, f"Chat error: {type(e).__name__}: {e}")

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Bench live ----------
    def do_bench_start(self) -> None:
        if self._bench_running:
            self._chat_log_system("Bench déjà en cours.")
            return
        self._bench_running = True

        bt = self.query_one("#bench_table", DataTable)
        bt.clear()

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
                self.call_from_thread(model_bar.update, total=100, progress=0)
                self.call_from_thread(role_bar.update, total=100, progress=0)

            elif evt == "role_start":
                # reset model bar for new role
                self.call_from_thread(model_bar.update, total=100, progress=0)

            elif evt == "model_start":
                # we don't have exact % steps without extra events; approximate with model_i/total_models
                i = int(payload.get("model_i", 0))
                n = int(payload.get("total_models", 1)) or 1
                pct = int((i / n) * 100)
                self.call_from_thread(role_bar.update, total=100, progress=pct)

            elif evt == "model_done":
                bt_payload = (
                    str(payload.get("role", "")),
                    str(payload.get("phase", "")),
                    str(payload.get("model", "")),
                    str(payload.get("score", "")),
                    str(payload.get("latency_ms", "")),
                    str(payload.get("status", "")),
                )
                self.call_from_thread(bt.add_row, *bt_payload)

        def worker() -> None:
            try:
                cache_dir = self.cfg.cache_root / "bench_runs" / "bench-standard"
                cache_dir.mkdir(parents=True, exist_ok=True)
                self.router.bench(
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
                self.call_from_thread(self._chat_log_system, "Bench terminé.")
            except Exception as e:
                self.call_from_thread(self._chat_log_system, f"Bench error: {type(e).__name__}: {e}")
            finally:
                self._bench_running = False

        threading.Thread(target=worker, daemon=True).start()

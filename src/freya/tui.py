# src/freya/tui.py
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path

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
)

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter
from .tools.webwatch import cyber_watch
from .tools.shell import run_powershell


# Nerd Font icons (best effort)
I_CHAT = "󰭹"
I_BENCH = "󱎴"
I_DEV = "󰨞"
I_SET = "󰒓"
I_FILE = "󰈙"
I_WATCH = "󰔚"


@dataclass
class ChatMsg:
    role: str
    content: str


PRESETS: dict[str, str] = {
    "Blue Hat (défense)": (
        "Tu es un assistant cybersécurité DEFENSIF (blue team). "
        "Objectif: durcissement, patching, audit, SOC, IR. "
        "Tu refuses toute demande illégale/offensive et proposes des alternatives défensives."
    ),
    "White Hat (pentest légal)": (
        "Tu es un assistant pour pentest légal et cadré. "
        "Tu aides sur la méthodologie, l'outillage légal, le reporting et la remédiation. "
        "Tu évites les détails directement exploitables."
    ),
    "Grey Hat (research)": (
        "Tu fais de la veille et du research: CVE, risques, mitigations, PoC high-level. "
        "Tu évites les instructions d'exploitation. Tu privilégies la défense."
    ),
    "Red Team (simulation autorisée)": (
        "Tu aides à simuler des scénarios autorisés (threat modeling, MITRE ATT&CK TTPs, "
        "détection, évaluation). Tu refuses toute aide illégale/offensive réelle."
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
    #left { width: 58%; }
    #right { width: 42%; border-left: solid gray; padding: 1; }

    #chat_controls { height: auto; }
    #chat_log { height: 1fr; }
    #chat_in { height: auto; }

    #artifact_list { height: 18; }
    #artifact_status { height: 3; color: $text-muted; }

    DataTable { height: 1fr; }
    RichLog { height: 1fr; }
    """

    BINDINGS = [
        ("ctrl+w", "cyber_watch", "Cyber Watch"),
        ("ctrl+o", "open_selected_artifact", "Open artifact"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.cfg = FreyaConfig.load()
        self.client = OllamaClient(base_url=self.cfg.ollama.base_url)
        self.router = LLMRouter(self.client)

        self.models: list[str] = []
        self.chat_history: list[ChatMsg] = []

        self.output_root: Path = self.cfg.artifacts_root
        self.selected_artifact: Path | None = None
        self._last_hover_id: str | None = None

    # ---------- UI ----------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main"):
            with Vertical(id="left"):
                with TabbedContent():
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
                            yield Button("PowerShell (approved)", id="btn_shell")

                        yield TextArea(id="custom_instructions")
                        yield RichLog(id="chat_log", wrap=True)
                        yield Input(placeholder="Message… (/watch)  — Ctrl+W: Cyber Watch", id="chat_in")

                    with TabPane(f"{I_BENCH} Benchmark", id="tab_bench"):
                        yield Static("Benchmark: table sortable/filters (brancher events bench ensuite).")
                        bt = DataTable(id="bench_table")
                        yield bt

                    with TabPane(f"{I_DEV} Webdeveloper (BMAD)", id="tab_webdev"):
                        yield Static(
                            "Webdeveloper (BMAD): chat dédié gestion de projet + actions guidées.\n"
                            "Prochain step: boutons 'générer artefacts', 'run cycle', 'open VS Code'."
                        )
                        yield RichLog(id="webdev_log", wrap=True)
                        yield Input(placeholder="Message gestion de projet…", id="webdev_in")

                    with TabPane(f"{I_SET} Settings", id="tab_settings"):
                        yield Static(
                            "Settings:\n"
                            "- Densité UI / couleurs (ici)\n"
                            "- Font-size / font-face = Windows Terminal\n"
                            "- Output root (artefacts)\n"
                        )

            with Vertical(id="right"):
                yield Static("BMAD artefacts / overview", id="right_title")
                yield Static(f"Output root: {self.output_root}", id="out_root")
                yield ScrollableContainer(id="artifact_list")
                yield Static("Hover: —\nSelected: —", id="artifact_status")

        yield Footer()

    def on_mount(self) -> None:
        # Models
        try:
            self.models = self.router.list_models()
        except Exception:
            self.models = []

        if not self.models:
            self.models = ["llama3.1:8b"]

        # Fill selects
        preset = self.query_one("#preset_select", Select)
        preset.value = "Blue Hat (défense)"

        primary = self.query_one("#primary_model", Select)
        summarizer = self.query_one("#summarizer_model", Select)

        primary.set_options([(m, m) for m in self.models])
        summarizer.set_options([(m, m) for m in self.models])

        primary.value = self._prefer_model(["llama3.1:8b", "mistral:7b", "qwen3:8b"])
        summarizer.value = self._prefer_model(["llama3.1:8b", "qwen2.5-coder:7b", "mistral:7b"])

        instr = self.query_one("#custom_instructions", TextArea)
        instr.border_title = "Instructions personnalisées (tu peux tout personnaliser)"
        instr.text = ""

        bt = self.query_one("#bench_table", DataTable)
        bt.add_columns("role", "phase", "model", "score", "latency_ms", "status")
        bt.cursor_type = "row"

        self._refresh_artifacts()
        self._chat_log("system", "Freya TUI prête. Chat en français. /watch pour l'actu cyber (sources officielles).")

    # ---------- Hover (mouse) ----------
    def on_mouse_move(self, event: events.MouseMove) -> None:
        # Best-effort hover: find widget under mouse
        try:
            widget, _region = self.screen.get_widget_at(event.screen_x, event.screen_y)
        except Exception:
            return

        if not isinstance(widget, Button):
            if self._last_hover_id is not None:
                self._last_hover_id = None
                self._set_artifact_status(hover="—", selected=str(self.selected_artifact) if self.selected_artifact else None)
            return

        wid = widget.id or ""
        if not wid.startswith("art_"):
            return

        if wid == self._last_hover_id:
            return
        self._last_hover_id = wid

        p_str = getattr(widget, "freya_path", None)
        if isinstance(p_str, str) and p_str:
            self._set_artifact_status(
                hover=Path(p_str).name,
                selected=str(self.selected_artifact) if self.selected_artifact else None,
            )

    # ---------- Helpers ----------
    def _prefer_model(self, candidates: list[str]) -> str:
        for c in candidates:
            if c in self.models:
                return c
        return self.models[0]

    def _chat_log(self, role: str, content: str) -> None:
        log = self.query_one("#chat_log", RichLog)
        log.write(f"[{role}] {content}")
        self.chat_history.append(ChatMsg(role=role, content=content))

    def _webdev_log(self, role: str, content: str) -> None:
        log = self.query_one("#webdev_log", RichLog)
        log.write(f"[{role}] {content}")

    # ---------- Artifacts ----------
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
        return files[:80]

    def _refresh_artifacts(self) -> None:
        container = self.query_one("#artifact_list", ScrollableContainer)
        container.remove_children()

        files = self._artifact_candidates()
        if not files:
            container.mount(Static("Aucun artefact trouvé (encore)."))
            return

        for p in files:
            label = f"{I_FILE} {p.name}"
            b = Button(label, id=f"art_{_safe_id(str(p))}")
            setattr(b, "freya_path", str(p))
            container.mount(b)

    def _set_artifact_status(self, hover: str | None = None, selected: str | None = None) -> None:
        st = self.query_one("#artifact_status", Static)
        hover_s = hover or "—"
        sel_s = selected or "—"
        st.update(f"Hover: {hover_s}\nSelected: {sel_s}")

    # ---------- Events ----------
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid == "btn_watch":
            self.do_cyber_watch()
            return

        if bid == "btn_shell":
            self._shell_status()
            return

        if bid.startswith("art_"):
            p_str = getattr(event.button, "freya_path", "")
            p = Path(p_str)
            if p.exists():
                self.selected_artifact = p
                self._set_artifact_status(selected=str(p))
                self._open_in_vscode(p)
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
            self._chat_generate(text)
            return

        if event.input.id == "webdev_in":
            self._webdev_log("user", text)
            self._webdev_log("assistant", "Reçu. (Prochaine étape: actions guidées BMAD + boutons.)")
            return

    # ---------- Actions ----------
    def action_open_selected_artifact(self) -> None:
        if self.selected_artifact and self.selected_artifact.exists():
            self._open_in_vscode(self.selected_artifact)

    def _open_in_vscode(self, path: Path) -> None:
        try:
            run_powershell(
                cmd=f'code -g "{path}"',
                audit_log=self.cfg.logs_root / "audit_shell.jsonl",
                timeout_sec=10,
                approved=True,
            )
        except Exception as e:
            self._chat_log("system", f"VS Code open error: {type(e).__name__}: {e}")

    # Main (business) cyber watch
    def do_cyber_watch(self) -> None:
        self._chat_log("system", "Cyber Watch: récupération (CISA KEV + CERT-FR)…")

        def worker() -> None:
            try:
                items = cyber_watch(self.cfg.cache_root / "web")
                lines = []
                for it in items[:12]:
                    lines.append(f"- [{it.source}] {it.title} ({it.published})\n  {it.url}")
                payload = "\n".join(lines)
                self.call_from_thread(self._chat_log, "tool", payload)

                prompt = (
                    "Voici des infos cyber récentes (sources officielles). "
                    "Fais un résumé en FR:\n"
                    "1) ce qui est critique\n"
                    "2) qui est impacté\n"
                    "3) actions défensives immédiates (patch/mitigation/détection)\n"
                    "4) priorisation.\n\n"
                    f"{payload}"
                )
                self.call_from_thread(self._chat_generate, prompt)
            except Exception as e:
                self.call_from_thread(self._chat_log, "system", f"Cyber Watch error: {type(e).__name__}: {e}")

        threading.Thread(target=worker, daemon=True).start()

    # Keybind handler (Ctrl+W)
    def action_cyber_watch(self) -> None:
        self.do_cyber_watch()

    def _shell_status(self) -> None:
        cmd = "freya status"
        try:
            res = run_powershell(
                cmd=cmd,
                audit_log=self.cfg.logs_root / "audit_shell.jsonl",
                timeout_sec=20,
                approved=True,
            )
            out = (res.stdout or res.stderr).strip()
            self._chat_log("tool", f"PS> {cmd}\n{out}")
        except Exception as e:
            self._chat_log("system", f"PowerShell tool error: {type(e).__name__}: {e}")

    def _system_prompt(self) -> str:
        preset_name = str(self.query_one("#preset_select", Select).value or "Blue Hat (défense)")
        preset_txt = PRESETS.get(preset_name, PRESETS["Blue Hat (défense)"])
        instr = self.query_one("#custom_instructions", TextArea).text or ""

        import datetime as dt
        today = dt.date.today().isoformat()

        return (
            "Tu es Freya. Tu réponds en français.\n"
            f"Date: {today}\n"
            f"Orientation: {preset_name}\n"
            f"{preset_txt}\n"
            "Règles: pas d'illégal, pas d'instructions d'attaque. Propose alternatives défensives.\n\n"
            "Instructions personnalisées:\n"
            f"{instr}\n"
        )

    def _chat_generate(self, user_text: str) -> None:
        def worker() -> None:
            try:
                system = self._system_prompt()
                primary = str(self.query_one("#primary_model", Select).value or self.models[0])
                summarizer = str(self.query_one("#summarizer_model", Select).value or primary)
                best_mode = bool(self.query_one("#best_models", Checkbox).value)

                primary_use = primary
                if best_mode and "dolphin-llama3:8b" in self.models:
                    primary_use = "dolphin-llama3:8b"

                res1 = self.client.generate(
                    model=primary_use,
                    prompt=user_text,
                    system=system,
                    options_extra={"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.05, "num_predict": 900},
                )
                answer = (res1.response or "").strip()

                res2 = self.client.generate(
                    model=summarizer,
                    prompt=(
                        "Résume et structure la réponse suivante en FR:\n"
                        "- TL;DR (3 lignes)\n"
                        "- Actions recommandées\n"
                        "- Points de vigilance\n\n"
                        f"{answer}"
                    ),
                    system="Tu es un summarizer. Très concis et structuré.",
                    options_extra={"temperature": 0.0, "top_p": 1.0, "repeat_penalty": 1.05, "num_predict": 450},
                )
                summary = (res2.response or "").strip()

                self.call_from_thread(self._chat_log, "assistant", f"{answer}\n\n---\nRésumé:\n{summary}")
            except Exception as e:
                self.call_from_thread(self._chat_log, "system", f"Chat error: {type(e).__name__}: {e}")

        threading.Thread(target=worker, daemon=True).start()

# src/freya/tui.py
from __future__ import annotations

import os
import datetime as dt
import json
import threading
import urllib.request
from dataclasses import dataclass
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Input, RichLog, Checkbox, Button, Static

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter


@dataclass
class ChatMsg:
    role: str
    content: str


def fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Freya/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


class FreyaTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #main { height: 1fr; }
    #left { width: 55%; }
    #right { width: 45%; }
    DataTable { height: 1fr; }
    RichLog { height: 1fr; }
    #controls { height: auto; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.cfg = FreyaConfig.load()
        self.client = OllamaClient(base_url=self.cfg.ollama.base_url)
        self.router = LLMRouter(self.client)

        self.chat: list[ChatMsg] = []
        self.chat_model_default = "llama3.1:8b"
        self.chat_model_uncensored = os.environ.get("FREYA_CHAT_MODEL_UNCENSORED", "dolphin-llama3:8b")
        self.uncensored = False

        self._bench_thread: threading.Thread | None = None
        self._bench_running = False

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="controls"):
            yield Checkbox("uncensored (cyber/white-hat)", id="uncensored")
            yield Button("Start bench-standard (bg)", id="start_bench")
            yield Button("Stop (soft)", id="stop_bench")
            yield Static(f"Date: {dt.datetime.now().isoformat(timespec='seconds')}", id="date")

        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield DataTable(id="bench_table")
            with Vertical(id="right"):
                yield RichLog(id="chat_log", wrap=True, highlight=True)
                yield Input(placeholder="Chat… (/watch pour veille CISA KEV)", id="chat_in")

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#bench_table", DataTable)
        table.add_columns("role", "phase", "model", "score", "latency_ms", "status")
        table.cursor_type = "row"
        self._log_chat("system", "Freya TUI ready. Toggle uncensored if needed. Use /watch for cyber watch (defensive).")

    def _log_chat(self, role: str, content: str) -> None:
        log = self.query_one("#chat_log", RichLog)
        log.write(f"[{role}] {content}")
        self.chat.append(ChatMsg(role=role, content=content))

    def _current_chat_model(self) -> str:
        return self.chat_model_uncensored if self.uncensored else self.chat_model_default

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "uncensored":
            self.uncensored = bool(event.value)
            self._log_chat("system", f"uncensored={'ON' if self.uncensored else 'OFF'} → model={self._current_chat_model()}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_bench":
            if self._bench_running:
                self._log_chat("system", "Bench already running.")
                return
            self._start_bench_bg()
        elif event.button.id == "stop_bench":
            self._log_chat("system", "Soft stop: use Ctrl+C in terminal if bench blocks hard (backend inference).")

    def _start_bench_bg(self) -> None:
        self._bench_running = True
        self._log_chat("system", "Starting bench-standard in background…")

        def worker() -> None:
            try:
                cache_dir = self.cfg.cache_root / "bench_runs" / "bench-standard"
                cache_dir.mkdir(parents=True, exist_ok=True)

                def progress(evt: str, payload: dict[str, Any]) -> None:
                    if evt == "model_done":
                        self.call_from_thread(self._bench_row_update, payload)

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

                self.call_from_thread(self._log_chat, "system", "Bench finished.")
            except Exception as e:
                self.call_from_thread(self._log_chat, "system", f"Bench error: {type(e).__name__}: {e}")
            finally:
                self._bench_running = False

        self._bench_thread = threading.Thread(target=worker, daemon=True)
        self._bench_thread.start()

    def _bench_row_update(self, payload: dict[str, Any]) -> None:
        table = self.query_one("#bench_table", DataTable)

        role = str(payload.get("role", ""))
        phase = str(payload.get("phase", ""))
        model = str(payload.get("model", ""))
        score = str(payload.get("score", ""))
        latency = str(payload.get("latency_ms", ""))
        status = str(payload.get("status", ""))

        # append rows; DataTable is scrollable by default (PgUp/PgDn/scroll)
        table.add_row(role, phase, model, score, latency, status)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return

        if text == "/watch":
            self._handle_watch()
            return

        self._log_chat("user", text)
        self._chat_generate(text)

    def _handle_watch(self) -> None:
        # Defensive sources only
        # CISA KEV JSON:
        # https://www.cisa.gov/known-exploited-vulnerabilities-catalog
        self._log_chat("system", "Fetching CISA KEV (defensive intel)…")
        try:
            kev = fetch_json("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
            vulns = kev.get("vulnerabilities", [])[:10]
            brief = "\n".join(
                f"- {v.get('cveID')} | {v.get('vendorProject')} {v.get('product')} | due: {v.get('dueDate')}"
                for v in vulns
            )
            self._log_chat("tool", "Top KEV:\n" + brief)
            self._chat_generate("Résume ces KEV en recommandations défensives (patch/hardening), sans détails d'exploitation.")
        except Exception as e:
            self._log_chat("system", f"Watch error: {type(e).__name__}: {e}")

    def _chat_generate(self, user_text: str) -> None:
        model = self._current_chat_model()

        system = (
            "You are Freya Chat. You are helpful and practical.\n"
            "Context: defensive cybersecurity / white-hat only.\n"
            f"Today is {dt.date.today().isoformat()}.\n"
            "If asked for offensive steps, refuse and provide safe defensive alternatives.\n"
        )

        prompt = user_text

        try:
            res = self.client.generate(
                model=model,
                prompt=prompt,
                system=system,
                options_extra={"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.05, "num_predict": 700},
            )
            self._log_chat("assistant", res.response.strip())
        except Exception as e:
            self._log_chat("system", f"Chat error: {type(e).__name__}: {e}")

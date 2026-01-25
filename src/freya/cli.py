from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter

console = Console()


def cmd_discover_models(_: argparse.Namespace) -> int:
    cfg = FreyaConfig.load()
    client = OllamaClient(base_url=cfg.ollama.base_url)
    router = LLMRouter(client)
    models = router.list_models()

    t = Table(title="Ollama models (installed)", show_lines=True)
    t.add_column("#", justify="right")
    t.add_column("name")
    for i, m in enumerate(models, start=1):
        t.add_row(str(i), m)
    console.print(t)
    return 0


def _bench(program: str, mode: str, trials: int, roles: list[str] | None) -> int:
    cfg = FreyaConfig.load()
    client = OllamaClient(base_url=cfg.ollama.base_url)
    router = LLMRouter(client)

    cache_dir = cfg.cache_root / "bench_runs" / program
    cache_dir.mkdir(parents=True, exist_ok=True)

    def progress(evt: str, payload: dict[str, Any]) -> None:
        if evt == "phase_start":
            console.rule(f"[bold]{payload.get('phase')}[/bold]")
        elif evt == "role_start":
            console.print(f"[cyan]{payload.get('role')}[/cyan] • {payload.get('phase')} • models={payload.get('total_models')}")
        elif evt == "model_done":
            console.print(
                f"  {payload.get('role')} / {payload.get('phase')} / {payload.get('model')}"
                f" => score={payload.get('score')} lat={payload.get('latency_ms')}ms ({payload.get('status')})"
            )

    scores = router.bench(
        roles=roles,
        models=None,
        max_models=0,
        trials=trials,
        mode=mode,
        cache_dir=cache_dir,
        resume=True,
        program=program,
        progress=progress,
    )

    summary = Table(title=f"Bench summary ({program})", show_lines=True)
    summary.add_column("role")
    summary.add_column("best_model")
    summary.add_column("score", justify="right")
    summary.add_column("latency_ms", justify="right")

    for role, lst in scores.items():
        if not lst:
            continue
        best = lst[0]
        summary.add_row(role, best.model, str(best.format_score), str(best.latency_ms))

    console.print(summary)
    return 0


def cmd_bench_fast(_: argparse.Namespace) -> int:
    return _bench("bench-fast", "quick", 1, None)


def cmd_bench_standard(_: argparse.Namespace) -> int:
    return _bench("bench-standard", "tune", 5, None)


def cmd_bench_advanced(_: argparse.Namespace) -> int:
    return _bench("bench-advanced", "tune", 5, None)


def cmd_tui(_: argparse.Namespace) -> int:
    from .tui import FreyaTUI

    FreyaTUI().run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="freya")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("discover-models")
    s.set_defaults(func=cmd_discover_models)

    s = sub.add_parser("bench-fast")
    s.set_defaults(func=cmd_bench_fast)

    s = sub.add_parser("bench-standard")
    s.set_defaults(func=cmd_bench_standard)

    s = sub.add_parser("bench-advanced")
    s.set_defaults(func=cmd_bench_advanced)

    s = sub.add_parser("tui")
    s.set_defaults(func=cmd_tui)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

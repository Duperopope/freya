# src/freya/cli.py
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter


console = Console()


def _cfg() -> FreyaConfig:
    return FreyaConfig.load()


def _comma_list(v: str | None) -> list[str] | None:
    if not v:
        return None
    items = [x.strip() for x in v.split(",")]
    items = [x for x in items if x]
    return items or None


def cmd_discover_models(args: argparse.Namespace) -> int:
    cfg = _cfg()
    client = OllamaClient(base_url=cfg.ollama.base_url)
    router = LLMRouter(client)

    models = router.list_models()

    table = Table(title="Ollama models (installed)", show_lines=True)
    table.add_column("#", justify="right")
    table.add_column("name")
    for i, m in enumerate(models, start=1):
        table.add_row(str(i), m)

    console.print(table)
    return 0


def _bench_common(
    program: str,
    mode: str,
    trials: int,
    roles: list[str] | None,
    max_models: int,
    resume: bool,
) -> int:
    cfg = _cfg()
    client = OllamaClient(base_url=cfg.ollama.base_url)
    router = LLMRouter(client)

    cache_dir = cfg.cache_root / "bench_runs" / program
    cache_dir.mkdir(parents=True, exist_ok=True)

    # progress callback (minimal; ta UI Rich live peut s’y brancher)
    def progress(evt: str, payload: dict[str, Any]) -> None:
        # on reste verbeux mais lisible: modèle courant + step_done
        if evt == "phase_start":
            console.rule(f"[bold]Phase[/bold] {payload.get('phase')}")
        elif evt == "role_start":
            console.print(
                f"[cyan]{payload.get('role')}[/cyan] • {payload.get('phase')} • "
                f"models={payload.get('total_models')} grid={payload.get('grid_n')} "
                f"cases={payload.get('cases_n')} trials={payload.get('trials')}"
            )
        elif evt == "model_start":
            console.print(
                f"  -> model {payload.get('model_i')}/{payload.get('total_models')}: [bold]{payload.get('model')}[/bold] "
                f"(steps_total={payload.get('steps_total')})"
            )
        elif evt == "step_done":
            # on n’affiche pas tout si ça spam; tu peux filtrer ici
            pass
        elif evt == "model_done":
            console.print(
                f"     done: score={payload.get('score')} latency={payload.get('latency_ms')}ms "
                f"status={payload.get('status')}"
            )
        elif evt == "interrupted":
            console.print(f"[yellow]Interrupted. State saved:[/yellow] {payload.get('state_path')}")

    scores = router.bench(
        roles=roles,
        models=None,                 # bench tous les installés
        max_models=max_models,
        trials=trials,
        mode=mode,
        cache_dir=cache_dir,
        resume=resume,
        program=program,
        progress=progress,
    )

    # Résumé final: meilleur modèle par rôle
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


def cmd_bench(args: argparse.Namespace) -> int:
    roles = _comma_list(args.roles)
    resume = not args.no_resume
    return _bench_common(
        program=args.program,
        mode=args.mode,
        trials=int(args.trials),
        roles=roles,
        max_models=int(args.max_models),
        resume=resume,
    )


def cmd_bench_fast(_: argparse.Namespace) -> int:
    return _bench_common(
        program="bench-fast",
        mode="quick",
        trials=1,
        roles=None,       # IMPORTANT: tous les rôles en fast
        max_models=0,     # 0 => pas de limite
        resume=True,
    )


def cmd_bench_standard(_: argparse.Namespace) -> int:
    return _bench_common(
        program="bench-standard",
        mode="tune",
        trials=5,
        roles=None,
        max_models=0,
        resume=True,
    )


def cmd_bench_advanced(_: argparse.Namespace) -> int:
    return _bench_common(
        program="bench-advanced",
        mode="tune",
        trials=5,
        roles=None,
        max_models=0,
        resume=True,
    )


def cmd_bench_planning(_: argparse.Namespace) -> int:
    return _bench_common(
        program="bench-planning",
        mode="tune",
        trials=5,
        roles=["analyst", "pm", "architect", "po", "sm"],
        max_models=0,
        resume=True,
    )


def cmd_bench_dev_stress(_: argparse.Namespace) -> int:
    return _bench_common(
        program="bench-dev-stress",
        mode="tune",
        trials=5,
        roles=["dev", "qa"],
        max_models=0,
        resume=True,
    )


def cmd_tui(_: argparse.Namespace) -> int:
    # Import tardif pour ne pas casser si textual pas installé
    from .tui import FreyaTUI

    app = FreyaTUI()
    app.run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="freya")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("discover-models", help="List installed Ollama models (no scraping)")
    s.set_defaults(func=cmd_discover_models)

    s = sub.add_parser("bench", help="Manual bench")
    s.add_argument("--mode", choices=["quick", "tune"], default="tune")
    s.add_argument("--trials", type=int, default=5)
    s.add_argument("--max-models", type=int, default=12)
    s.add_argument("--roles", type=str, default="")
    s.add_argument("--program", type=str, default="bench-manual")
    s.add_argument("--no-resume", action="store_true", default=False)
    s.set_defaults(func=cmd_bench)

    s = sub.add_parser("bench-fast", help="Phase1_fast only (all roles)")
    s.set_defaults(func=cmd_bench_fast)

    s = sub.add_parser("bench-standard", help="Phase1_fast + Phase2_coarse (all roles)")
    s.set_defaults(func=cmd_bench_standard)

    s = sub.add_parser("bench-advanced", help="Phase1_fast + Phase2_coarse + Phase3_advanced (all roles)")
    s.set_defaults(func=cmd_bench_advanced)

    s = sub.add_parser("bench-planning", help="Planning roles only")
    s.set_defaults(func=cmd_bench_planning)

    s = sub.add_parser("bench-dev-stress", help="Dev + QA roles only")
    s.set_defaults(func=cmd_bench_dev_stress)

    s = sub.add_parser("tui", help="One-window TUI: chat + bench (best practice)")
    s.set_defaults(func=cmd_tui)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .config import FreyaConfig
from .ollama_client import OllamaClient
from .router import LLMRouter, ModelScore

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


def _write_routing(cache_root: Path, scores: dict[str, list[ModelScore]]) -> Path:
    """
    Persist best-per-role routing to cache_root/routing.json
    Compatible with Orchestrator.model_for_role/options_for_role.
    """
    routing: dict[str, Any] = {}
    for role, lst in scores.items():
        if not lst:
            continue
        best = lst[0]
        routing[role] = {"model": best.model, "options": dict(best.options or {})}

    out = cache_root / "routing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(routing, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _bench(program: str, mode: str, trials: int, roles: list[str] | None, apply_routing: bool) -> int:
    cfg = FreyaConfig.load()
    client = OllamaClient(base_url=cfg.ollama.base_url)
    router = LLMRouter(client)

    cache_dir = cfg.cache_root / "bench_runs" / program
    cache_dir.mkdir(parents=True, exist_ok=True)

    def progress(evt: str, payload: dict[str, Any]) -> None:
        if evt == "phase_start":
            console.rule(f"[bold]{payload.get('phase')}[/bold]")
        elif evt == "role_start":
            console.print(
                f"[cyan]{payload.get('role')}[/cyan] • {payload.get('phase')} • models={payload.get('total_models')}"
            )
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

    if apply_routing:
        p = _write_routing(cfg.cache_root, scores)
        console.print(f"[green]routing.json mis à jour:[/green] {p}")

    return 0


def cmd_bench_fast(args: argparse.Namespace) -> int:
    return _bench("bench-fast", "quick", 1, None, bool(args.apply_routing))


def cmd_bench_standard(args: argparse.Namespace) -> int:
    return _bench("bench-standard", "tune", 5, None, bool(args.apply_routing))


def cmd_bench_advanced(args: argparse.Namespace) -> int:
    return _bench("bench-advanced", "tune", 5, None, bool(args.apply_routing))


def cmd_autopilot(args: argparse.Namespace) -> int:
    from .autopilot import AutopilotConfig, FreyaAutopilot

    cfg = FreyaConfig.load()

    default_base = getattr(cfg, "artifacts_root", cfg.cache_root) / "projects"
    output_dir = Path(args.output).resolve() if args.output else (default_base / args.name).resolve()

    console.rule("[bold]Freya Autopilot[/bold]")
    console.print(f"[dim]Output:[/dim] {output_dir}")
    console.print(f"[dim]Name:[/dim] {args.name}")
    console.print(f"[dim]Max fix iters:[/dim] {args.max_fix_iters}")

    ap_cfg = AutopilotConfig(
        goal=str(args.goal),
        output_dir=str(output_dir),
        project_name=str(args.name),
        max_fix_iters=int(args.max_fix_iters),
        open_vscode=not bool(args.no_vscode),
    )

    FreyaAutopilot(ap_cfg).run()
    console.print("[green]OK: projet généré + tests passés.[/green]")
    return 0


def cmd_tui(_: argparse.Namespace) -> int:
    """Launch the legacy TUI (requires textual)."""
    try:
        from .tui import FreyaTUI
        FreyaTUI().run()
        return 0
    except ImportError:
        console.print("[red]Error:[/red] TUI requires 'textual'. Install with: pip install freya[tui]")
        return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the Freya Web API server."""
    import uvicorn
    from pathlib import Path
    
    host = args.host
    port = args.port
    debug = args.debug
    
    console.rule("[bold cyan]Freya Web Server v2.0[/bold cyan]")
    console.print(f"[dim]Host:[/dim] {host}")
    console.print(f"[dim]Port:[/dim] {port}")
    console.print(f"[dim]Debug:[/dim] {debug}")
    
    # Check for static files (built web UI)
    web_dist = Path(__file__).parent.parent.parent / "web" / "dist"
    static_found = web_dist.exists() and (web_dist / "index.html").exists()
    
    if static_found:
        console.print(f"[green]Web UI:[/green] {web_dist}")
    else:
        console.print(f"[yellow]Web UI not built.[/yellow] Run: cd web && npm install && npm run build")
        console.print(f"[dim]API-only mode enabled.[/dim]")
    
    console.print()
    console.print(f"[bold green]Server starting at http://{host}:{port}[/bold green]")
    if debug:
        console.print(f"[dim]API docs: http://{host}:{port}/api/docs[/dim]")
    console.print()
    
    # Determine which app factory to use
    if debug:
        app_target = "freya.api.main:create_app"
        factory = True
    else:
        # Production mode with static files
        app_target = "freya.api.main:create_production_app"
        factory = True
    
    # Run uvicorn
    uvicorn.run(
        app_target,
        factory=factory,
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="freya")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("discover-models")
    s.set_defaults(func=cmd_discover_models)

    s = sub.add_parser("bench-fast")
    s.add_argument("--apply-routing", action="store_true", help="Écrit cache_root/routing.json avec les meilleurs modèles.")
    s.set_defaults(func=cmd_bench_fast)

    s = sub.add_parser("bench-standard")
    s.add_argument("--apply-routing", action="store_true", help="Écrit cache_root/routing.json avec les meilleurs modèles.")
    s.set_defaults(func=cmd_bench_standard)

    s = sub.add_parser("bench-advanced")
    s.add_argument("--apply-routing", action="store_true", help="Écrit cache_root/routing.json avec les meilleurs modèles.")
    s.set_defaults(func=cmd_bench_advanced)

    s = sub.add_parser("autopilot")
    s.add_argument("--goal", required=True, help="Objectif produit en français.")
    s.add_argument("--name", required=False, default="FreyaApp", help="Nom du projet.")
    s.add_argument("--output", required=False, help="Dossier de sortie (sinon base Freya).")
    s.add_argument("--max-fix-iters", type=int, default=3, help="Itérations max de correction.")
    s.add_argument("--no-vscode", action="store_true", help="Ne pas ouvrir VS Code.")
    s.set_defaults(func=cmd_autopilot)

    s = sub.add_parser("tui", help="Launch legacy TUI (requires textual)")
    s.set_defaults(func=cmd_tui)

    # Web server command
    s = sub.add_parser("serve", help="Start the Freya Web API server")
    s.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    s.add_argument("--port", "-p", type=int, default=8765, help="Port to listen on (default: 8765)")
    s.add_argument("--debug", "-d", action="store_true", help="Enable debug mode with auto-reload")
    s.set_defaults(func=cmd_serve)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

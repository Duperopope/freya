# src/freya/router.py
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .benchmarkq import default_bench_suite, eval_text_against_case
from .ollama_client import OllamaClient


ProgressCb = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class ModelScore:
    model: str
    latency_ms: int
    format_score: int
    role: str
    options: dict[str, Any]


def _key(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", errors="ignore"))
        h.update(b"\x1f")
    return h.hexdigest()[:20]


_INVALID_WIN = re.compile(r'[<>:"/\\|?*\x00-\x1F]+')


def _safe_slug(name: str, max_len: int = 80) -> str:
    """
    Windows-safe slug for folder/file names.
    """
    s = name.strip()
    s = _INVALID_WIN.sub("_", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" ", "_")
    s = re.sub(r"_+", "_", s)
    if not s:
        s = "empty"
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s


@dataclass(frozen=True)
class BenchPhase:
    name: str
    trials: int
    grid: list[dict[str, Any]]
    # keep_top_n = None => keep all models for next phase
    keep_top_n: int | None = None
    # timeout per generate call (seconds). None/0 => no timeout
    timeout_sec: int | None = None


class LLMRouter:
    """
    Bench + routing for BMAD roles using Ollama (and later other providers).
    """

    def __init__(self, client: OllamaClient):
        self.client = client
        self.scores: dict[str, list[ModelScore]] = {}

    def list_models(self) -> list[str]:
        tags = self.client.tags()

        models: list[str] = []

        # tags peut être dict (attendu) ou list (selon ton client/wrapper)
        if isinstance(tags, dict):
            items = tags.get("models", [])
        elif isinstance(tags, list):
            items = tags
        else:
            items = []

        for m in items:
            if not isinstance(m, dict):
                continue
            name = m.get("name") or m.get("model")
            if isinstance(name, str) and name:
                models.append(name)

        return sorted(set(models), key=str.lower)

    def _default_param_grid(self, mode: str) -> list[dict[str, Any]]:
        # "quick" => one deterministic setting
        if mode == "quick":
            return [
                {"temperature": 0.0, "top_p": 1.0, "repeat_penalty": 1.05, "num_predict": 650}
            ]
        # "tune" => coarse grid
        return [
            {"temperature": 0.0, "top_p": 1.0, "repeat_penalty": 1.05, "num_predict": 650},
            {"temperature": 0.2, "top_p": 0.95, "repeat_penalty": 1.07, "num_predict": 750},
            {"temperature": 0.4, "top_p": 0.9, "repeat_penalty": 1.10, "num_predict": 850},
            {"temperature": 0.6, "top_p": 0.85, "repeat_penalty": 1.12, "num_predict": 950},
        ]

    def _default_phases(self, program: str, mode: str, trials: int) -> list[BenchPhase]:
        """
        A single suite split into phases; still assigns ALL BMAD roles in every phase.
        """
        # You asked: "tous les fast en premier", then coarse, then advanced.
        # - bench-fast => phase1 only
        # - bench-standard => phase1 + phase2
        # - bench-advanced => phase1 + phase2 + phase3
        grid_fast = self._default_param_grid("quick")
        grid_coarse = self._default_param_grid(mode)

        phases: list[BenchPhase] = []

        # Phase 1: very fast sanity
        phases.append(
            BenchPhase(
                name="phase1_fast",
                trials=1,
                grid=grid_fast,
                keep_top_n=None,  # keep all into coarse by default (no dataset reset needed)
                timeout_sec=int(os.environ.get("FREYA_BENCH_TIMEOUT_FAST", "0")) or None,
            )
        )

        if program in ("bench-standard", "bench-advanced", "bench-manual"):
            phases.append(
                BenchPhase(
                    name="phase2_coarse",
                    trials=max(1, trials),
                    grid=grid_coarse,
                    keep_top_n=int(os.environ.get("FREYA_BENCH_KEEP_COARSE", "6")),
                    timeout_sec=int(os.environ.get("FREYA_BENCH_TIMEOUT_COARSE", "0")) or None,
                )
            )

        if program in ("bench-advanced",):
            # Advanced: more trials + slightly wider grid
            grid_adv = grid_coarse + [
                {"temperature": 0.8, "top_p": 0.8, "repeat_penalty": 1.15, "num_predict": 1100},
                {"temperature": 0.15, "top_p": 0.98, "repeat_penalty": 1.05, "num_predict": 900},
            ]
            phases.append(
                BenchPhase(
                    name="phase3_advanced",
                    trials=max(7, trials),
                    grid=grid_adv,
                    keep_top_n=int(os.environ.get("FREYA_BENCH_KEEP_ADV", "3")),
                    timeout_sec=int(os.environ.get("FREYA_BENCH_TIMEOUT_ADV", "0")) or None,
                )
            )

        return phases

    def bench(
        self,
        *,
        roles: list[str] | None = None,
        models: list[str] | None = None,
        max_models: int = 12,
        trials: int = 5,
        mode: str = "tune",
        cache_dir: Path,
        resume: bool = True,
        program: str = "bench-standard",
        progress: ProgressCb | None = None,
    ) -> dict[str, list[ModelScore]]:
        """
        Multi-phase, phase-major benchmark:
          phase1_fast: all roles, all models
          phase2_coarse: all roles, narrowed models (optional keep_top_n)
          phase3_advanced: all roles, narrowed models (optional keep_top_n)

        Writes:
          cache_dir/bench_state.json (resume)
          cache_dir/bench_raw/<role>/<phase>/<model>/<case>/trialN.(txt|json)
        """
        cache_dir.mkdir(parents=True, exist_ok=True)
        raw_root = cache_dir / "bench_raw"
        raw_root.mkdir(parents=True, exist_ok=True)
        state_path = cache_dir / "bench_state.json"

        suite = default_bench_suite()
        wanted_roles = roles or sorted(set(c.role for c in suite))
        suite = [c for c in suite if c.role in wanted_roles]

        installed = models or self.list_models()
        if max_models and len(installed) > max_models:
            installed = installed[:max_models]

        # Load state for resume
        state: dict[str, Any] = {"done": {}, "meta": {}}
        if resume and state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                if "done" not in state or not isinstance(state["done"], dict):
                    state["done"] = {}
            except Exception:
                state = {"done": {}, "meta": {}}

        state["meta"] = {
            "program": program,
            "mode": mode,
            "trials": trials,
            "max_models": max_models,
            "roles": wanted_roles,
            "updated_at": time.time(),
        }

        phases = self._default_phases(program, mode, trials)

        # candidates_by_role starts with all models for all roles
        candidates_by_role: dict[str, list[str]] = {r: list(installed) for r in wanted_roles}

        # For final results: best per role across last executed phase
        best_by_role: dict[str, ModelScore] = {}

        def save_state() -> None:
            state["meta"]["updated_at"] = time.time()
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

        try:
            # PHASE-MAJOR LOOP (your requested order)
            for phase in phases:
                if progress:
                    progress("phase_start", {"phase": phase.name, "roles": wanted_roles})

                for role in wanted_roles:
                    cases = [c for c in suite if c.role == role]
                    if not cases:
                        continue

                    candidates = candidates_by_role.get(role, [])
                    if progress:
                        progress(
                            "role_start",
                            {
                                "role": role,
                                "phase": phase.name,
                                "total_models": len(candidates),
                                "cases_n": len(cases),
                                "grid_n": len(phase.grid),
                                "trials": phase.trials,
                            },
                        )

                    scored_models: list[ModelScore] = []

                    for model_i, model in enumerate(candidates, start=1):
                        steps_total = len(phase.grid) * len(cases) * phase.trials
                        if progress:
                            progress(
                                "model_start",
                                {
                                    "role": role,
                                    "phase": phase.name,
                                    "model": model,
                                    "model_i": model_i,
                                    "total_models": len(candidates),
                                    "steps_total": steps_total,
                                },
                            )

                        best_score = -10**9
                        best_latency = 10**9
                        best_opts: dict[str, Any] = {}

                        total_score_for_best = -10**9
                        total_latency_for_best = 10**9

                        # Evaluate grid; choose grid setting that maximizes total score over all cases & trials
                        for grid_i, opts in enumerate(phase.grid, start=1):
                            total_score = 0
                            total_latency = 0
                            ok_all = True
                            notes_all: list[str] = []

                            for case in cases:
                                for t in range(1, phase.trials + 1):
                                    # Unique resume key
                                    k = _key(
                                        program,
                                        role,
                                        phase.name,
                                        model,
                                        case.name,
                                        str(t),
                                        json.dumps(opts, sort_keys=True),
                                    )

                                    # If done, reuse
                                    if k in state["done"]:
                                        rec = state["done"][k]
                                        total_score += int(rec.get("score", 0))
                                        total_latency += int(rec.get("latency_ms", 0))
                                        ok_all = ok_all and bool(rec.get("ok", True))
                                        continue

                                    # Run
                                    started = time.perf_counter()
                                    ok = True
                                    score = -999999
                                    latency_ms = 999999
                                    notes = ""

                                    try:
                                        sys_prompt = (
                                            f"You are generating a BMAD {role} artifact. "
                                            f"Follow requirements precisely."
                                        )

                                        # Ollama API supports options per request
                                        # Ref: https://github.com/ollama/ollama/blob/main/docs/api.md
                                        res = self.client.generate(
                                            model=model,
                                            prompt=case.prompt,
                                            system=sys_prompt,
                                            options_extra=opts,
                                            timeout_sec=phase.timeout_sec,
                                        )
                                        text = res.response
                                        latency_ms = int(res.duration_ms)
                                        ev = eval_text_against_case(text, case)
                                        score = int(ev.score)
                                        ok = bool(ev.ok)
                                        notes = ev.notes or ""
                                    except KeyboardInterrupt:
                                        raise
                                    except Exception as e:
                                        ok = False
                                        notes = f"exception: {type(e).__name__}: {e}"

                                    ended = time.perf_counter()
                                    if latency_ms == 999999:
                                        latency_ms = int((ended - started) * 1000)

                                    # Write raw
                                    role_slug = _safe_slug(role)
                                    phase_slug = _safe_slug(phase.name)
                                    model_slug = _safe_slug(model)
                                    case_slug = _safe_slug(case.name)
                                    out_dir = raw_root / role_slug / phase_slug / model_slug / case_slug
                                    out_dir.mkdir(parents=True, exist_ok=True)

                                    (out_dir / f"trial{t}.txt").write_text(
                                        text if "text" in locals() else "", encoding="utf-8", errors="ignore"
                                    )
                                    (out_dir / f"trial{t}.json").write_text(
                                        json.dumps(
                                            {
                                                "program": program,
                                                "role": role,
                                                "phase": phase.name,
                                                "model": model,
                                                "case": case.name,
                                                "trial": t,
                                                "options": opts,
                                                "score": score,
                                                "ok": ok,
                                                "notes": notes,
                                                "latency_ms": latency_ms,
                                            },
                                            indent=2,
                                        ),
                                        encoding="utf-8",
                                    )

                                    # Save in state
                                    state["done"][k] = {
                                        "score": score,
                                        "ok": ok,
                                        "notes": notes,
                                        "latency_ms": latency_ms,
                                    }
                                    save_state()

                                    total_score += score
                                    total_latency += latency_ms
                                    ok_all = ok_all and ok
                                    if notes:
                                        notes_all.append(notes)

                                    if progress:
                                        progress(
                                            "step_done",
                                            {
                                                "role": role,
                                                "phase": phase.name,
                                                "model": model,
                                                "grid_i": grid_i,
                                                "grid_n": len(phase.grid),
                                                "case": case.name,
                                                "trial": t,
                                                "trials": phase.trials,
                                                "delta_score": score,
                                                "latency_ms": latency_ms,
                                            },
                                        )

                            # pick best grid setting for this model
                            # primary: higher score, tie-break: lower latency
                            if total_score > total_score_for_best or (
                                total_score == total_score_for_best and total_latency < total_latency_for_best
                            ):
                                total_score_for_best = total_score
                                total_latency_for_best = total_latency
                                best_opts = dict(opts)
                                best_score = total_score
                                best_latency = total_latency
                            if not ok_all and notes_all:
                                pass

                        ms = ModelScore(
                            model=model,
                            latency_ms=int(best_latency),
                            format_score=int(best_score),
                            role=role,
                            options=best_opts,
                        )
                        scored_models.append(ms)

                        if progress:
                            progress(
                                "model_done",
                                {
                                    "role": role,
                                    "phase": phase.name,
                                    "model": model,
                                    "score": ms.format_score,
                                    "latency_ms": ms.latency_ms,
                                    "status": "ok" if ms.format_score > -999999 else "error",
                                    "options": ms.options,
                                },
                            )

                    # Sort by score desc then latency asc
                    scored_models.sort(key=lambda x: (-x.format_score, x.latency_ms))
                    # Store scores for role (we keep per-run phase results by overwriting role list)
                    self.scores[role] = scored_models

                    # Keep best for routing summary
                    if scored_models:
                        best_by_role[role] = scored_models[0]

                    # Narrow candidates for next phase if requested
                    if phase.keep_top_n is not None and phase.keep_top_n > 0:
                        candidates_by_role[role] = [m.model for m in scored_models[: phase.keep_top_n]]
                    else:
                        candidates_by_role[role] = [m.model for m in scored_models]

                    if progress:
                        progress(
                            "role_done",
                            {
                                "role": role,
                                "phase": phase.name,
                                "top_model": best_by_role[role].model if role in best_by_role else None,
                            },
                        )

                if progress:
                    progress("phase_done", {"phase": phase.name})

        except KeyboardInterrupt:
            save_state()
            if progress:
                progress("interrupted", {"where": "bench", "state_path": str(state_path)})
            raise

        return self.scores

    def pick(self, role: str, fallback: str | None = None, mode: str = "balanced") -> str:
        scores = self.scores.get(role, [])
        if scores:
            return scores[0].model
        if fallback:
            return fallback
        # last-resort: pick any model
        models = self.list_models()
        return models[0] if models else ""

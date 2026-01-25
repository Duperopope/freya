from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchCase:
    role: str
    name: str
    prompt: str
    required_regex: list[str]
    min_bullets: int = 0
    must_contain_tokens: list[str] | None = None
    min_numbers: int = 0  # require numeric thresholds/metrics
    forbid_regex: list[str] | None = None


@dataclass(frozen=True)
class BenchEval:
    ok: bool
    score: int
    notes: str


_REFUSAL_RE = re.compile(r"\b(as an ai|i cannot|i can't|i'm unable|je ne peux pas|désolé)\b", re.IGNORECASE)
_CODEBLOCK_RE = re.compile(r"```", re.MULTILINE)


def _count_bullets(text: str) -> int:
    n = 0
    for line in (text or "").splitlines():
        s = line.strip()
        if re.match(r"^(\-|\*|\d+\.)\s+\S+", s):
            n += 1
    return n


def _count_numbers(text: str) -> int:
    # counts numeric tokens, percentages, comparisons
    if not text:
        return 0
    hits = re.findall(r"(\d+(\.\d+)?\s*%|\b\d+(\.\d+)?\b|[<>]=?\s*\d+)", text)
    return len(hits)


def extract_fullfile_blocks(text: str) -> list[tuple[str, str]]:
    pattern = r"FREYA_FULLFILE:\s*(.+?)\s*\n```(?:\w+)?\n(.*?)\n```"
    matches = re.findall(pattern, text or "", flags=re.DOTALL)
    return [(p.strip(), c) for (p, c) in matches]


def python_compiles(code: str) -> bool:
    try:
        compile(code, "<freya-bench>", "exec")
        return True
    except Exception:
        return False


def eval_text_against_case(text: str, case: BenchCase) -> BenchEval:
    t = (text or "").strip()
    low = t.lower()

    score = 0
    notes: list[str] = []

    if _REFUSAL_RE.search(t):
        score -= 10
        notes.append("refusal_or_fluff")

    # Required regex markers
    for rx in case.required_regex:
        if re.search(rx, t, flags=re.MULTILINE):
            score += 3
        else:
            score -= 3
            notes.append(f"missing:{rx}")

    # Forbidden regex
    for rx in (case.forbid_regex or []):
        if re.search(rx, t, flags=re.MULTILINE | re.IGNORECASE):
            score -= 3
            notes.append(f"forbidden:{rx}")

    # Must contain tokens
    for tok in (case.must_contain_tokens or []):
        if tok.lower() in low:
            score += 1
        else:
            score -= 1
            notes.append(f"missing_token:{tok}")

    # Bullets
    if case.min_bullets > 0:
        b = _count_bullets(t)
        if b >= case.min_bullets:
            score += 3
            notes.append(f"bullets_ok:{b}")
        else:
            score -= 3
            notes.append(f"bullets_low:{b}<{case.min_bullets}")

    # Numeric thresholds
    if case.min_numbers > 0:
        n = _count_numbers(t)
        if n >= case.min_numbers:
            score += 3
            notes.append(f"numbers_ok:{n}")
        else:
            score -= 3
            notes.append(f"numbers_low:{n}<{case.min_numbers}")

    # Role-specific deep checks
    if case.role == "dev":
        blocks = extract_fullfile_blocks(t)
        if not blocks:
            score -= 12
            notes.append("no_fullfile_blocks")
        else:
            py = [(p, c) for (p, c) in blocks if p.lower().endswith(".py")]
            if not py:
                score -= 6
                notes.append("no_python_files")
            else:
                bad = 0
                for p, c in py[:10]:
                    if not python_compiles(c):
                        bad += 1
                        notes.append(f"compile_fail:{p}")
                if bad == 0:
                    score += 6
                    notes.append("compile_ok")
                else:
                    score -= 6

            if any(p.replace("\\", "/").startswith("tests/") for (p, _) in blocks):
                score += 3
                notes.append("has_tests")
            else:
                score -= 3
                notes.append("missing_tests")

    if case.role == "qa":
        # require explicit OK/NOK verdict
        if re.search(r"(?im)^\s*##\s*verdict\s*$", t) and re.search(r"\b(OK|NOK)\b", t, re.IGNORECASE):
            score += 4
        else:
            score -= 4
            notes.append("missing_verdict_ok_nok")

        # require traceability-looking lines (e.g. FR-1 -> tests/...)
        if re.search(r"(?im)(FR-\d+|NFR-\d+)\s*->\s*tests?/", t):
            score += 2
        else:
            score -= 2
            notes.append("weak_traceability")

    ok = score >= 6
    return BenchEval(ok=ok, score=score, notes=";".join(notes))


def default_bench_suite() -> list[BenchCase]:
    """
    Discriminant BMAD-tailored suite (EN skeleton for stable parsing).
    """
    suite: list[BenchCase] = []

    # Analyst: skeleton + measurable risks/metrics/hypotheses
    suite.append(
        BenchCase(
            role="analyst",
            name="brief_skeleton",
            prompt=(
                "Return EXACTLY this Markdown skeleton, then fill it with concise bullet points.\n"
                "# project-brief\n"
                "## vision\n"
                "## target users\n"
                "## key use cases\n"
                "## constraints\n"
                "## risks & mitigations\n"
                "## success metrics\n"
            ),
            required_regex=[
                r"(?im)^#\s*project-brief\s*$",
                r"(?im)^##\s*vision\s*$",
                r"(?im)^##\s*key\s+use\s+cases\s*$",
                r"(?im)^##\s*risks\s*&\s*mitigations\s*$",
                r"(?im)^##\s*success\s+metrics\s*$",
            ],
            min_bullets=10,
            must_contain_tokens=["Windows", "Ollama", "VS Code", "BMAD"],
            min_numbers=0,
        )
    )
    suite.append(
        BenchCase(
            role="analyst",
            name="brief_measurable",
            prompt=(
                "Write ONLY this section (no extra headings):\n"
                "## risks & mitigations\n"
                "Provide exactly 5 risks.\n"
                "Each risk must include: impact, mitigation, and a measurable metric with a numeric threshold.\n"
                "Example metric formats: '< 2s', '> 95%', '>= 10 GB free'.\n"
            ),
            required_regex=[r"(?im)^##\s*risks\s*&\s*mitigations\s*$"],
            min_bullets=10,
            min_numbers=5,
        )
    )

    # PM: PRD with FR/NFR and measurable AC
    suite.append(
        BenchCase(
            role="pm",
            name="prd_skeleton",
            prompt=(
                "Return EXACTLY this Markdown skeleton, then fill it.\n"
                "# PRD\n"
                "## problem statement\n"
                "## goals / non-goals\n"
                "## functional requirements\n"
                "## non-functional requirements\n"
                "## epics\n"
            ),
            required_regex=[
                r"(?im)^#\s*PRD\s*$",
                r"(?im)^##\s*functional\s+requirements\s*$",
                r"(?im)^##\s*non-functional\s+requirements\s*$",
                r"(?im)^##\s*epics\s*$",
            ],
            min_bullets=12,
            must_contain_tokens=["local", "Ollama", "Windows"],
        )
    )
    suite.append(
        BenchCase(
            role="pm",
            name="prd_acceptance_criteria",
            prompt=(
                "Write:\n"
                "## functional requirements\n"
                "Provide 6 FR items labeled FR-1..FR-6.\n"
                "Each FR must include Acceptance Criteria with at least 1 numeric threshold.\n"
            ),
            required_regex=[r"(?im)^##\s*functional\s+requirements\s*$", r"(?im)\bFR-1\b", r"(?im)\bFR-6\b"],
            min_bullets=12,
            min_numbers=6,
        )
    )

    # Architect: module boundaries + safety + observability (concrete)
    suite.append(
        BenchCase(
            role="architect",
            name="arch_core",
            prompt=(
                "Return EXACTLY this Markdown skeleton and fill it with concrete module boundaries and interfaces.\n"
                "# architecture\n"
                "## stack\n"
                "## module boundaries\n"
                "## artifact flow (BMAD)\n"
                "## safety model\n"
                "## logging & observability\n"
            ),
            required_regex=[
                r"(?im)^#\s*architecture\s*$",
                r"(?im)^##\s*module\s+boundaries\s*$",
                r"(?im)^##\s*safety\s+model\s*$",
                r"(?im)^##\s*logging\s*&\s*observability\s*$",
            ],
            min_bullets=14,
            must_contain_tokens=["artifacts", ".freya", "logs"],
        )
    )
    suite.append(
        BenchCase(
            role="architect",
            name="arch_security_ops",
            prompt=(
                "Write ONLY:\n"
                "## safety model\n"
                "Include allowlist/denylist paths concept, 'never delete' rules, and 'dry run'.\n"
                "Also write ONLY:\n"
                "## logging & observability\n"
                "Include jsonl events + run reports.\n"
            ),
            required_regex=[
                r"(?im)^##\s*safety\s+model\s*$",
                r"(?im)^##\s*logging\s*&\s*observability\s*$",
            ],
            min_bullets=10,
            must_contain_tokens=["allowlist", "denylist", "dry run", "jsonl"],
        )
    )

    # PO: shard to epics with story IDs
    suite.append(
        BenchCase(
            role="po",
            name="po_epic_format",
            prompt=(
                "Output exactly 3 epics, each separated by '===EPIC==='.\n"
                "Each epic must start with '# epic: <slug>' and include:\n"
                "## goal\n## scope\n## dependencies\n## stories\n"
                "Stories must be bullet list with IDs like 1.1, 1.2 ...\n"
            ),
            required_regex=[r"(?im)^#\s*epic:\s*.+$", r"(?im)^##\s*stories\s*$", r"(?m)\b1\.1\b"],
            min_bullets=12,
        )
    )

    # SM: story file with steps + tests
    suite.append(
        BenchCase(
            role="sm",
            name="sm_story_quality",
            prompt=(
                "Output exactly 1 story.\n"
                "Format:\n"
                "# story: 1.1 Something\n"
                "## context\n"
                "## technical notes\n"
                "## implementation steps\n"
                "## acceptance criteria\n"
                "## tests\n"
                "Steps must be numbered 1..6 and mention file paths.\n"
                "Tests must mention pytest.\n"
            ),
            required_regex=[
                r"(?im)^#\s*story:\s*1\.1\s+.+$",
                r"(?im)^##\s*implementation\s+steps\s*$",
                r"(?im)^##\s*tests\s*$",
                r"(?m)^\s*1\.\s+",
                r"(?m)^\s*6\.\s+",
            ],
            min_bullets=10,
            must_contain_tokens=["tests/", "pytest"],
        )
    )

    # DEV: strict fullfile + compile + tests
    suite.append(
        BenchCase(
            role="dev",
            name="dev_fullfile_compile",
            prompt=(
                "You MUST output ONLY FREYA_FULLFILE blocks.\n"
                "Create two files:\n"
                "1) src/freya_demo/mathx.py with add(a,b)->a+b\n"
                "2) tests/test_mathx.py with pytest test asserting add(1,2)==3\n"
                "No extra text.\n"
            ),
            required_regex=[r"(?m)^\s*FREYA_FULLFILE:\s*.+$"],
            forbid_regex=[r"```diff", r"(?i)\bhere is\b"],
        )
    )

    # QA: gates + traceability + verdict
    suite.append(
        BenchCase(
            role="qa",
            name="qa_report_traceability",
            prompt=(
                "Return EXACTLY:\n"
                "# QA report\n"
                "## gates\n"
                "## issues\n"
                "## traceability\n"
                "## verdict\n"
                "In traceability, include lines like 'FR-1 -> tests/test_x.py::test_y'.\n"
                "Verdict must be OK or NOK.\n"
            ),
            required_regex=[r"(?im)^#\s*QA\s+report\s*$", r"(?im)^##\s*traceability\s*$"],
            min_bullets=8,
            min_numbers=0,
        )
    )

    return suite

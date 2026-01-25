from __future__ import annotations

from pathlib import Path
from .base import BaseAgent, AgentContext
from ..quality import QualityGate


class QAAgent(BaseAgent):
    def __init__(self, *args, quality: QualityGate, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.quality = quality

    def run(self, ctx: AgentContext) -> Path:
        system = (
            "You are BMAD QA.\n"
            "Produce a QA report with gates, issues, traceability and a final verdict OK/NOK.\n"
            "Follow the exact headings.\n"
        )

        ruff_ok, ruff_out = self.quality.run_ruff()
        pytest_ok, pytest_out = self.quality.run_pytest()

        prompt = f"""
Tool outputs:

Ruff ok: {ruff_ok}
---
{ruff_out}
---

Pytest ok: {pytest_ok}
---
{pytest_out}
---

Return EXACTLY this Markdown skeleton and fill it:

# QA report
## gates
## issues
## traceability
## verdict
"""
        report = self._gen(role="qa", prompt=prompt.strip(), system=system)
        if not report.lower().startswith("# qa report"):
            report = "# QA report\n\n" + report

        out = ctx.artifacts_root / "QA.md"
        return self._write(out, report + "\n")

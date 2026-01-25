from __future__ import annotations

from pathlib import Path
from .base import BaseAgent, AgentContext


class ArchitectAgent(BaseAgent):
    def run(self, ctx: AgentContext) -> Path:
        prd = ctx.artifacts_root / "PRD.md"
        out = ctx.artifacts_root / "architecture.md"

        system = (
            "You are BMAD Architect. Produce architecture.md as a standalone Markdown artifact.\n"
            "Follow the exact skeleton headings.\n"
        )

        prompt = f"""
Input: PRD.md
---
{self._read(prd)}
---

Return EXACTLY this Markdown skeleton, then fill it with concrete module/file suggestions:

# architecture
## stack
## module boundaries
## artifact flow (BMAD)
## safety model
## logging & observability
"""
        content = self._gen(role="architect", prompt=prompt.strip(), system=system)
        if not content.lower().startswith("# architecture"):
            content = "# architecture\n\n" + content
        return self._write(out, content + "\n")

from __future__ import annotations

from pathlib import Path
from .base import BaseAgent, AgentContext


class PMAgent(BaseAgent):
    def run(self, ctx: AgentContext) -> Path:
        brief = ctx.artifacts_root / "project-brief.md"
        out = ctx.artifacts_root / "PRD.md"

        system = (
            "You are BMAD PM. Produce PRD.md as a standalone Markdown artifact.\n"
            "Follow the exact skeleton headings.\n"
        )

        prompt = f"""
Input: project-brief.md
---
{self._read(brief)}
---

Return EXACTLY this Markdown skeleton, then fill it with bullet points:

# PRD
## problem statement
## goals / non-goals
## functional requirements
## non-functional requirements
## epics
"""
        content = self._gen(role="pm", prompt=prompt.strip(), system=system)
        if not content.lower().startswith("# prd"):
            content = "# PRD\n\n" + content
        return self._write(out, content + "\n")

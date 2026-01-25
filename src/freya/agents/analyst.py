from __future__ import annotations

from pathlib import Path
from .base import BaseAgent, AgentContext


class AnalystAgent(BaseAgent):
    def run(self, ctx: AgentContext) -> Path:
        out = ctx.artifacts_root / "project-brief.md"
        system = (
            "You are BMAD Analyst. Produce a standalone Markdown artifact.\n"
            "Follow the exact skeleton headings.\n"
        )
        prompt = f"""
Goal (Sam): {ctx.goal}

Return EXACTLY this Markdown skeleton, then fill it with concise bullet points:

# project-brief
## vision
## target users
## key use cases
## constraints
## risks & mitigations
## success metrics
"""
        content = self._gen(role="analyst", prompt=prompt.strip(), system=system)
        if not content.lower().startswith("# project-brief"):
            content = "# project-brief\n\n" + content
        return self._write(out, content + "\n")

from __future__ import annotations

import re
from pathlib import Path
from .base import BaseAgent, AgentContext


class ProductOwnerAgent(BaseAgent):
    def run(self, ctx: AgentContext) -> Path:
        prd = ctx.artifacts_root / "PRD.md"
        arch = ctx.artifacts_root / "architecture.md"
        out_dir = ctx.artifacts_root / "epics"
        out_dir.mkdir(parents=True, exist_ok=True)

        system = (
            "You are BMAD Product Owner. Shard PRD+Architecture into multiple epic files.\n"
            "Each epic must start with '# epic: <slug>'.\n"
        )

        prompt = f"""
Inputs:
--- PRD.md ---
{self._read(prd)}
--- architecture.md ---
{self._read(arch)}
---

Create 3 to 7 epics. Output format:

===EPIC===
# epic: <slug>
## goal
## scope
## out of scope
## dependencies
## stories
- 1.1 <story title>
- 1.2 <story title>
"""
        txt = self._gen(role="po", prompt=prompt.strip(), system=system)

        chunks = [c.strip() for c in txt.split("===EPIC===") if c.strip()]
        written = 0
        for c in chunks:
            m = re.search(r"^#\s*epic:\s*(.+)$", c, flags=re.MULTILINE | re.IGNORECASE)
            if not m:
                continue
            slug = m.group(1).strip().lower()
            slug = re.sub(r"[^a-z0-9\-_. ]+", "", slug).strip().replace(" ", "-")
            slug = re.sub(r"-+", "-", slug) or "epic"
            p = out_dir / f"epic-{slug}.md"
            self._write(p, c + "\n")
            written += 1

        index = ctx.artifacts_root / "epics.md"
        lines = ["# epics", "", f"- count: {written}", ""]
        for p in sorted(out_dir.glob("epic-*.md")):
            lines.append(f"- {p.name}")
        return self._write(index, "\n".join(lines) + "\n")

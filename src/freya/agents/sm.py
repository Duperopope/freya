from __future__ import annotations

import re
from pathlib import Path
from .base import BaseAgent, AgentContext


class ScrumMasterAgent(BaseAgent):
    def run(self, ctx: AgentContext) -> Path:
        epics_dir = ctx.artifacts_root / "epics"
        stories_dir = ctx.artifacts_root / "stories"
        stories_dir.mkdir(parents=True, exist_ok=True)

        epic_files = sorted(epics_dir.glob("epic-*.md"))
        if not epic_files:
            raise FileNotFoundError("No epics found. Run PO sharding first.")

        system = (
            "You are BMAD Scrum Master. Convert epics into detailed story files.\n"
            "Each story must be standalone Markdown starting with '# story: <id> <title>'.\n"
            "Follow the exact headings in each story.\n"
        )

        written = 0
        for epic_file in epic_files:
            epic_txt = self._read(epic_file)
            prompt = f"""
Input epic: {epic_file.name}
---
{epic_txt}
---

Create 2 to 6 story documents. Output format:

===STORY===
# story: <id> <title>
## context
## technical notes
## implementation steps
## acceptance criteria
## tests
"""
            txt = self._gen(role="sm", prompt=prompt.strip(), system=system)
            stories = [s.strip() for s in txt.split("===STORY===") if s.strip()]

            for s in stories:
                m = re.search(r"^#\s*story:\s*([0-9]+\.[0-9]+)\s*(.+)$", s, flags=re.MULTILINE | re.IGNORECASE)
                if not m:
                    continue
                sid = m.group(1)
                title = m.group(2).strip()
                safe_title = re.sub(r"[^a-z0-9\-_. ]+", "", title.lower()).strip().replace(" ", "-")
                safe_title = re.sub(r"-+", "-", safe_title)[:60] or "story"
                p = stories_dir / f"{sid}.{safe_title}.story.md"
                self._write(p, s + "\n")
                written += 1

        index = ctx.artifacts_root / "stories.md"
        lines = ["# stories", "", f"- count: {written}", ""]
        for p in sorted(stories_dir.glob("*.story.md")):
            lines.append(f"- {p.name}")
        return self._write(index, "\n".join(lines) + "\n")

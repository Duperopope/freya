from __future__ import annotations

import logging
import re
from pathlib import Path
from .base import BaseAgent, AgentContext

logger = logging.getLogger("freya.agents.sm")


class ScrumMasterAgent(BaseAgent):
    def run(self, ctx: AgentContext) -> Path:
        epics_dir = ctx.artifacts_root / "epics"
        stories_dir = ctx.artifacts_root / "stories"
        stories_dir.mkdir(parents=True, exist_ok=True)

        # Find epic files - check both patterns
        epic_files = sorted(epics_dir.glob("epic-*.md"))
        if not epic_files:
            epic_files = sorted(epics_dir.glob("*.md"))
        
        # If still no files, check if there's an epics.md in artifacts root
        if not epic_files:
            epics_md = ctx.artifacts_root / "epics.md"
            if epics_md.exists():
                logger.info(f"[SM] Using epics.md as source: {epics_md}")
                epic_files = [epics_md]
        
        if not epic_files:
            raise FileNotFoundError(f"No epics found in {epics_dir}. Run PO sharding first.")

        system = (
            "You are BMAD Scrum Master. Convert epics into detailed story files.\n"
            "Each story must be standalone Markdown starting with '# story: <id> <title>'.\n"
            "Follow the exact headings in each story.\n"
        )

        written = 0
        for epic_idx, epic_file in enumerate(epic_files):
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
            logger.info(f"[SM] Generated text length: {len(txt)} chars for {epic_file.name}")
            
            # Try multiple split patterns
            stories = [s.strip() for s in txt.split("===STORY===") if s.strip()]
            
            # If no ===STORY=== markers, try splitting by "# story" or "## Story"
            if len(stories) <= 1:
                stories = re.split(r"(?=^#{1,2}\s*story)", txt, flags=re.MULTILINE | re.IGNORECASE)
                stories = [s.strip() for s in stories if s.strip()]
            
            # If still no split, treat entire output as one story
            if not stories:
                stories = [txt.strip()]
            
            logger.info(f"[SM] Found {len(stories)} stories in {epic_file.name}")

            for idx, s in enumerate(stories):
                if not s or len(s) < 20:  # Skip empty or too short
                    continue
                    
                # Try multiple patterns to match story header
                m = re.search(r"^#\s*story[:\s]*([0-9]+(?:\.[0-9]+)?)\s*[:\-]?\s*(.*)$", s, flags=re.MULTILINE | re.IGNORECASE)
                if not m:
                    # Try alternative pattern: "# Story 1: Title" or "# 1.1 Title"
                    m = re.search(r"^#\s*(?:story\s+)?([0-9]+(?:\.[0-9]+)?)[:\s]+(.*)$", s, flags=re.MULTILINE | re.IGNORECASE)
                if not m:
                    # Try "## Story: Title"
                    m = re.search(r"^#{1,3}\s*(?:story|user story)[:\s]*(.*)$", s, flags=re.MULTILINE | re.IGNORECASE)
                    if m:
                        sid = f"{epic_idx + 1}.{idx + 1}"
                        title = m.group(1).strip()
                    else:
                        # Fallback: use epic number + index
                        epic_num = re.search(r"epic-?(\d+)", epic_file.name, re.IGNORECASE)
                        epic_id = epic_num.group(1) if epic_num else str(epic_idx + 1)
                        sid = f"{epic_id}.{idx + 1}"
                        # Try to extract title from first heading
                        title_match = re.search(r"^#\s+(.+)$", s, flags=re.MULTILINE)
                        title = title_match.group(1).strip() if title_match else f"story-{idx + 1}"
                else:
                    sid = m.group(1)
                    title = m.group(2).strip() if m.group(2) else f"story-{sid}"
                
                # Sanitize title for filename
                safe_title = re.sub(r"[^a-z0-9\-_. ]+", "", title.lower()).strip().replace(" ", "-")
                safe_title = re.sub(r"-+", "-", safe_title)[:60] or "story"
                p = stories_dir / f"{sid}.{safe_title}.story.md"
                self._write(p, s + "\n")
                logger.info(f"[SM] Wrote story: {p.name}")
                written += 1

        index = ctx.artifacts_root / "stories.md"
        lines = ["# stories", "", f"- count: {written}", ""]
        for p in sorted(stories_dir.glob("*.story.md")):
            lines.append(f"- {p.name}")
        return self._write(index, "\n".join(lines) + "\n")

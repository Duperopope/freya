from __future__ import annotations

from pathlib import Path
from .base import BaseAgent, AgentContext
from ..quality import QualityGate


class DeveloperAgent(BaseAgent):
    def __init__(self, *args, quality: QualityGate, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.quality = quality

    def run_one_story(self, ctx: AgentContext, story_path: Path) -> str:
        story = self._read(story_path)

        system = (
            "You are BMAD Developer.\n"
            "You MUST output ONLY FREYA_FULLFILE blocks for each file you create/modify.\n"
            "Protocol:\n"
            "FREYA_FULLFILE: relative/path.py\n"
            "```python\n"
            "<full file content>\n"
            "```\n"
            "No extra text outside those blocks.\n"
        )

        prompt = f"""
Story:
--- {story_path.name} ---
{story}
---

Implement the story. Keep code minimal but production-grade.
If creating Python code, include tests in tests/ and keep pytest passing.
"""
        out_text = self._gen(role="dev", prompt=prompt.strip(), system=system)
        changed = self.quality.apply_unified_diff(ctx.workspace_root, out_text)
        return "Changed files:\n- " + "\n- ".join(str(p.relative_to(ctx.workspace_root)) for p in changed)

    def run(self, ctx: AgentContext) -> Path:
        stories_dir = ctx.artifacts_root / "stories"
        story_files = sorted(stories_dir.glob("*.story.md"))
        if not story_files:
            # Check if stories directory exists and what's in it
            if not stories_dir.exists():
                raise FileNotFoundError(f"Stories directory not found: {stories_dir}. SM agent may have failed.")
            existing = list(stories_dir.glob("*"))
            raise FileNotFoundError(f"No story files found in {stories_dir}. Found: {[f.name for f in existing[:5]]}. SM agent may have generated invalid format.")

        out = ctx.artifacts_root / "dev-log.md"
        lines: list[str] = ["# dev-log", ""]

        for sp in story_files:
            lines.append(f"## {sp.name}")
            try:
                lines.append(self.run_one_story(ctx, sp))
            except Exception as e:
                lines.append(f"ERROR implementing story: {e}")
            lines.append("")

        return self._write(out, "\n".join(lines) + "\n")

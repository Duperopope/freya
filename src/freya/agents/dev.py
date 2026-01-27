from __future__ import annotations

import logging
from pathlib import Path
from .base import BaseAgent, AgentContext
from ..quality import QualityGate

logger = logging.getLogger("freya.agents.dev")


class DeveloperAgent(BaseAgent):
    def __init__(self, *args, quality: QualityGate, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.quality = quality

    def run_one_story(self, ctx: AgentContext, story_path: Path) -> str:
        story = self._read(story_path)
        
        # Get architecture context if available
        arch_file = ctx.artifacts_root / "architecture.md"
        arch_context = ""
        if arch_file.exists():
            arch_content = self._read(arch_file)
            arch_context = f"\n\nArchitecture context:\n{arch_content[:2000]}...\n"

        system = (
            "You are BMAD Developer. You write production-grade code.\n"
            "You MUST output code in this EXACT format for EACH file:\n\n"
            "FREYA_FULLFILE: path/to/file.py\n"
            "```python\n"
            "# Full file content here\n"
            "```\n\n"
            "Rules:\n"
            "- Create complete, runnable files\n"
            "- Include proper imports at the top\n"
            "- Use type hints for Python\n"
            "- Create tests in tests/ directory\n"
            "- Create a main.py or app.py as entry point\n"
            "- No explanations, ONLY FREYA_FULLFILE blocks\n"
        )

        prompt = f"""
Story to implement:
--- {story_path.name} ---
{story}
---
{arch_context}
Create the necessary files. Output FREYA_FULLFILE blocks for each file.
Include:
1. Main application code
2. Tests in tests/ folder
3. Requirements in requirements.txt if needed
"""
        logger.info(f"[Dev] Generating code for story: {story_path.name}")
        out_text = self._gen(role="dev", prompt=prompt.strip(), system=system)
        
        # Write to BOTH workspace (for execution) and artifacts/code (for display)
        code_dir = ctx.artifacts_root / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # First write to artifacts/code for visibility
        changed_artifacts = self.quality.apply_unified_diff(code_dir, out_text)
        
        # Also write to workspace for execution (if different)
        changed_workspace = []
        if ctx.workspace_root != code_dir:
            try:
                changed_workspace = self.quality.apply_unified_diff(ctx.workspace_root, out_text)
            except Exception as e:
                logger.warning(f"[Dev] Could not write to workspace: {e}")
        
        all_changed = changed_artifacts + changed_workspace
        
        if not all_changed:
            logger.warning(f"[Dev] No files generated for story: {story_path.name}")
            # Save raw output for debugging
            debug_file = ctx.artifacts_root / "code" / f"_debug_{story_path.stem}.txt"
            debug_file.write_text(f"Raw LLM output:\n\n{out_text}", encoding="utf-8")
            return f"WARNING: No code files extracted. Raw output saved to {debug_file.name}"
        
        result = "Generated files:\n"
        for p in changed_artifacts:
            try:
                rel = p.relative_to(ctx.artifacts_root)
                result += f"- {rel}\n"
            except ValueError:
                result += f"- {p.name}\n"
        
        return result

    def run(self, ctx: AgentContext) -> Path:
        stories_dir = ctx.artifacts_root / "stories"
        story_files = sorted(stories_dir.glob("*.story.md"))
        
        # Fallback: check for any .md files in stories dir
        if not story_files:
            story_files = sorted(stories_dir.glob("*.md"))
        
        # Fallback 2: use stories.md from artifacts root
        if not story_files:
            stories_md = ctx.artifacts_root / "stories.md"
            if stories_md.exists() and stories_md.stat().st_size > 50:
                logger.info(f"[Dev] Using stories.md as fallback: {stories_md}")
                story_files = [stories_md]
        
        # Fallback 3: use PRD.md or architecture.md to generate code directly
        if not story_files:
            prd_file = ctx.artifacts_root / "PRD.md"
            arch_file = ctx.artifacts_root / "architecture.md"
            if prd_file.exists():
                logger.info(f"[Dev] Using PRD.md as source (no stories available)")
                story_files = [prd_file]
            elif arch_file.exists():
                logger.info(f"[Dev] Using architecture.md as source (no stories available)")
                story_files = [arch_file]
        
        if not story_files:
            # Check if stories directory exists and what's in it
            if not stories_dir.exists():
                logger.error(f"Stories directory not found: {stories_dir}")
                raise FileNotFoundError(f"Stories directory not found: {stories_dir}. SM agent may have failed.")
            existing = list(stories_dir.glob("*"))
            logger.error(f"No story files in {stories_dir}. Found: {[f.name for f in existing[:10]]}")
            raise FileNotFoundError(f"No story files found in {stories_dir}. Found: {[f.name for f in existing[:5]]}. SM agent may have generated invalid format.")

        out = ctx.artifacts_root / "dev-log.md"
        lines: list[str] = ["# Development Log", "", f"Generated at: {__import__('datetime').datetime.now().isoformat()}", ""]
        
        code_dir = ctx.artifacts_root / "code"
        total_files = 0

        for sp in story_files:
            lines.append(f"## Story: {sp.name}")
            logger.info(f"[Dev] Processing story: {sp.name}")
            try:
                result = self.run_one_story(ctx, sp)
                lines.append(result)
                # Count generated files
                total_files += len([f for f in code_dir.rglob("*") if f.is_file() and not f.name.startswith("_debug")])
            except Exception as e:
                error_msg = f"ERROR implementing story: {e}"
                logger.error(f"[Dev] {error_msg}", exc_info=True)
                lines.append(error_msg)
            lines.append("")

        # Summary
        all_code_files = list(code_dir.rglob("*"))
        code_files = [f for f in all_code_files if f.is_file() and not f.name.startswith("_debug")]
        
        lines.append("## Summary")
        lines.append(f"- Stories processed: {len(story_files)}")
        lines.append(f"- Code files generated: {len(code_files)}")
        lines.append("")
        lines.append("### Generated Files:")
        for f in code_files:
            try:
                rel = f.relative_to(ctx.artifacts_root)
                lines.append(f"- `{rel}`")
            except ValueError:
                lines.append(f"- `{f.name}`")

        return self._write(out, "\n".join(lines) + "\n")

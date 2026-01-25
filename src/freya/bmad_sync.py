from __future__ import annotations

import io
import zipfile
import requests
import shutil
import subprocess
from pathlib import Path


BMAD_GITHUB_REPO = "https://github.com/bmad-code-org/BMAD-METHOD"
BMAD_ZIP = "https://github.com/bmad-code-org/BMAD-METHOD/archive/refs/heads/main.zip"


class BMADSync:
    def __init__(self, bmad_root: Path) -> None:
        self.bmad_root = bmad_root.resolve()

    def sync(self) -> str:
        self.bmad_root.mkdir(parents=True, exist_ok=True)
        target = self.bmad_root / "BMAD-METHOD"

        git = shutil.which("git")
        if git:
            if target.exists() and (target / ".git").exists():
                cp = subprocess.run([git, "-C", str(target), "pull"], capture_output=True, text=True)
                if cp.returncode == 0:
                    return f"BMAD synced via git pull: {target}"
                # fallback to zip if pull fails
            else:
                cp = subprocess.run([git, "clone", BMAD_GITHUB_REPO, str(target)], capture_output=True, text=True)
                if cp.returncode == 0:
                    return f"BMAD cloned: {target}"
                # fallback

        # ZIP fallback
        r = requests.get(BMAD_ZIP, timeout=120)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        tmp = self.bmad_root / "_tmp_zip_extract"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True, exist_ok=True)
        z.extractall(tmp)

        extracted = next(tmp.glob("BMAD-METHOD-*"), None)
        if extracted is None:
            raise RuntimeError("BMAD zip extract failed: folder not found")

        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(extracted), str(target))
        shutil.rmtree(tmp, ignore_errors=True)
        return f"BMAD synced via zip: {target}"

    def locate_templates_dir(self) -> Path:
        """
        BMAD repo structure may evolve. We locate docs/templates heuristically.
        """
        root = self.bmad_root / "BMAD-METHOD"
        if not root.exists():
            raise FileNotFoundError("BMAD repo not present. Run sync first.")
        return root

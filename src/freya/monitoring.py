from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import psutil


@dataclass(frozen=True)
class MachineStatus:
    cpu_percent: float
    ram_percent: float
    disk_free_gb: float
    disk_total_gb: float


class Monitor:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def snapshot(self) -> MachineStatus:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        du = shutil.disk_usage(str(self.workspace_root))
        free_gb = du.free / (1024**3)
        total_gb = du.total / (1024**3)
        return MachineStatus(cpu_percent=cpu, ram_percent=ram, disk_free_gb=free_gb, disk_total_gb=total_gb)

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "freya.log"
    events_file = log_dir / "events.jsonl"

    logger = logging.getLogger("freya")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    class JsonlHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                payload = {
                    "ts": utc_iso(),
                    "level": record.levelname,
                    "msg": record.getMessage(),
                    "name": record.name,
                }
                with open(events_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except Exception:
                pass

    logger.addHandler(JsonlHandler())
    return logger

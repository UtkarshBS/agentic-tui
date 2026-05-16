"""Structured JSONL logging."""
import json
import datetime
from pathlib import Path


class Logger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._file = self.log_dir / f"session_{datetime.datetime.now().isoformat()}.jsonl"
        self._fh = self._file.open("a", encoding="utf-8")

    def log(self, event_type: str, payload: dict):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": event_type,
            "payload": payload,
        }
        self._fh.write(json.dumps(entry, default=str) + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()

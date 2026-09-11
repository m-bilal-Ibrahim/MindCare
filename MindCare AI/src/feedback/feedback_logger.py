"""Append structured psychologist review feedback as JSON Lines."""

import json
from pathlib import Path
from typing import Any


def log_feedback(record: dict[str, Any], path: str | Path) -> Path:
    """Append one feedback record and return the log path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as feedback_file:
        feedback_file.write(json.dumps(record) + "\n")
    return destination

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import isodate


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def parse_since(value: str) -> datetime:
    now = datetime.now().astimezone()
    if value.startswith("P"):
        return now - isodate.parse_duration(value)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=now.tzinfo)
    return parsed.astimezone()


def parse_timestamp(value: str, reference: datetime) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=reference.tzinfo)
    return parsed.astimezone(reference.tzinfo)


class TimeWindowQuery:
    def __init__(self, *, since: str, q: str | None) -> None:
        self.since = parse_since(since)
        self.q = q.casefold() if q else None

    def includes(self, row: dict[str, Any], *, timestamp_key: str) -> bool:
        timestamp = parse_timestamp(row[timestamp_key], self.since)
        if timestamp < self.since:
            return False
        if self.q is None:
            return True
        return self.q in json.dumps(row, sort_keys=True).casefold()

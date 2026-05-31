from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

import isodate
from browser_history import utils

from keep_up_with.integrations.base import ToolContext, tool


@tool("Search local browser history.")
def history(
    _ctx: ToolContext,
    since: str = "P30D",
    limit: int = 100,
    q: str | None = None,
) -> list[dict[str, Any]]:
    query = HistoryQuery(since=since, q=q)
    rows: list[dict[str, Any]] = []
    for browser_class in utils.get_browsers():
        try:
            browser = browser_class()
        except AssertionError:
            continue
        if not browser.history_dir.exists():
            continue
        try:
            visits = browser.fetch_history(sort=False).histories
        except (OSError, sqlite3.Error):
            continue
        for visited_at, url, *rest in visits:
            row = {
                "browser": browser_class.name,
                "title": rest[0] if rest else "",
                "url": url,
                "visited_at": visited_at.isoformat(),
            }
            if query.includes(row):
                rows.append(row)
    return sorted(rows, key=lambda row: row["visited_at"])[-max(1, min(limit, 1000)) :]


class HistoryQuery:
    def __init__(self, *, since: str, q: str | None) -> None:
        self.since = parse_since(since)
        self.q = q.casefold() if q else None

    def includes(self, row: dict[str, Any]) -> bool:
        visited_at = parse_visited_at(row["visited_at"], self.since)
        if visited_at < self.since:
            return False
        if self.q is None:
            return True
        return self.q in json.dumps(row, sort_keys=True).casefold()


def parse_since(value: str) -> datetime:
    now = datetime.now().astimezone()
    if value.startswith("P"):
        return now - isodate.parse_duration(value)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=now.tzinfo)
    return parsed.astimezone()


def parse_visited_at(value: str, reference: datetime) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=reference.tzinfo)
    return parsed.astimezone(reference.tzinfo)

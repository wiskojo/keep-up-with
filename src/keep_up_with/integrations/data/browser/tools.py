from __future__ import annotations

import sqlite3
from typing import Any

from browser_history import utils

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import TimeWindowQuery


@tool("Search local browser history.")
def history(
    _ctx: ToolContext,
    since: str = "P30D",
    limit: int = 100,
    q: str | None = None,
) -> list[dict[str, Any]]:
    query = TimeWindowQuery(since=since, q=q)
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
            if query.includes(row, timestamp_key="visited_at"):
                rows.append(row)
    return sorted(rows, key=lambda row: row["visited_at"])[-max(1, min(limit, 1000)) :]

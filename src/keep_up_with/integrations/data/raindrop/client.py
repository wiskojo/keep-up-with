from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import httpx

from keep_up_with.integrations.data.common import TimeWindowQuery


def bookmarks(
    token: str,
    *,
    since: str = "P30D",
    limit: int = 100,
    q: str | None = None,
) -> list[dict[str, Any]]:
    query = TimeWindowQuery(since=since, q=q)
    events: list[dict[str, Any]] = []
    page = 0
    per_page = 50

    while True:
        response = httpx.get(
            "https://api.raindrop.io/rest/v1/raindrops/0",
            params={"search": "", "page": page, "perpage": per_page},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        response.raise_for_status()
        payload = cast("dict[str, object]", response.json())

        items = payload.get("items")
        if not isinstance(items, list) or not items:
            return events

        for item in cast("list[dict[str, object]]", items):
            event = bookmark_event(item)
            if event:
                events.append(event)

        if len(items) < per_page:
            break
        page += 1

    return sorted(
        (event for event in events if query.includes(event, timestamp_key="created_at")),
        key=lambda event: event["created_at"],
    )[-limit:]


def bookmark_event(item: dict[str, object]) -> dict[str, Any] | None:
    created = item.get("created")
    url = item.get("link")
    if not isinstance(created, str) or not isinstance(url, str):
        return None
    try:
        created_at = datetime.fromisoformat(created).isoformat()
    except ValueError:
        return None
    return {
        "url": url,
        "title": item.get("title") or "",
        "tags": item.get("tags") or [],
        "created_at": created_at,
    }

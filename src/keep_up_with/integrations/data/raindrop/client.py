from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast

import httpx
import isodate


def bookmarks(
    token: str,
    *,
    since: str = "P30D",
    limit: int = 100,
    q: str | None = None,
) -> list[dict[str, Any]]:
    query = BookmarkQuery(since=since, q=q)
    events: list[dict[str, Any]] = []
    page = 0
    per_page = 50

    while True:
        try:
            response = httpx.get(
                "https://api.raindrop.io/rest/v1/raindrops/0",
                params={"search": "", "page": page, "perpage": per_page},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            if response.status_code >= 400:
                return events
            payload = cast("dict[str, object]", response.json())
        except (httpx.HTTPError, json.JSONDecodeError):
            return events

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
        (event for event in events if query.includes(event)),
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


class BookmarkQuery:
    def __init__(self, *, since: str, q: str | None) -> None:
        self.since = parse_since(since)
        self.q = q.casefold() if q else None

    def includes(self, event: dict[str, Any]) -> bool:
        created_at = parse_created_at(event["created_at"], self.since)
        if created_at < self.since:
            return False
        if self.q is None:
            return True
        return self.q in json.dumps(event, sort_keys=True).casefold()


def parse_since(value: str) -> datetime:
    now = datetime.now().astimezone()
    if value.startswith("P"):
        return now - isodate.parse_duration(value)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=now.tzinfo)
    return parsed.astimezone()


def parse_created_at(value: str, reference: datetime) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=reference.tzinfo)
    return parsed.astimezone(reference.tzinfo)

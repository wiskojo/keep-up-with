from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.raindrop import client


@tool("Search Raindrop bookmarks")
def bookmarks(
    ctx: ToolContext,
    since: str = "P30D",
    limit: int = 100,
    q: str | None = None,
) -> list[dict[str, Any]]:
    return client.bookmarks(ctx.env("RAINDROP_TOKEN"), since=since, limit=limit, q=q)

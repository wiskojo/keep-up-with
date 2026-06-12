from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.youtube import client


@tool("Search YouTube")
def search(
    ctx: ToolContext,
    query: str,
    limit: int = 10,
    order: str = "relevance",
    result_type: str = "video",
    channel: str = "",
    published_after: str = "",
    published_before: str = "",
) -> list[dict[str, Any]]:
    return client.search(
        ctx.env("YOUTUBE_API_KEY"),
        query,
        limit=limit,
        order=order,
        result_type=result_type,
        channel=channel,
        published_after=published_after,
        published_before=published_before,
    )


@tool("Show channel metadata and videos")
def channel(ctx: ToolContext, channel: str, limit: int = 10) -> dict[str, Any]:
    return client.channel(
        ctx.env("YOUTUBE_API_KEY"),
        channel,
        limit=limit,
    )

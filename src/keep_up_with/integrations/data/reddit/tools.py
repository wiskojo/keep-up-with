from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.reddit.client import RedditClient


def client(ctx: ToolContext) -> RedditClient:
    return RedditClient(
        client_id=ctx.env("REDDIT_CLIENT_ID"),
        client_secret=ctx.env("REDDIT_CLIENT_SECRET"),
    )


@tool("List posts from a subreddit.")
def posts(
    ctx: ToolContext,
    subreddit: str,
    sort: str = "hot",
    period: str = "day",
    limit: int = 25,
) -> list[dict[str, Any]]:
    return client(ctx).posts(subreddit, sort=sort, period=period, limit=limit)


@tool("Search Reddit posts.")
def search(
    ctx: ToolContext,
    query: str,
    subreddit: str | None = None,
    sort: str = "relevance",
    period: str = "all",
    limit: int = 25,
) -> list[dict[str, Any]]:
    return client(ctx).search(
        query,
        subreddit=subreddit,
        sort=sort,
        period=period,
        limit=limit,
    )


@tool("Fetch a Reddit post and nested comments.")
def thread(
    ctx: ToolContext,
    url_or_id: str,
    sort: str = "best",
    depth: int = 3,
    limit: int = 100,
) -> dict[str, Any]:
    return client(ctx).thread(url_or_id, sort=sort, depth=depth, limit=limit)

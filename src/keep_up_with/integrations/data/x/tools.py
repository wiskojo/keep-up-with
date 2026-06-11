from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.x.client import XClient


def client(ctx: ToolContext) -> XClient:
    return XClient(ctx.env("X_BEARER_TOKEN"))


@tool("Search X posts")
def search(ctx: ToolContext, query: str, limit: int = 10) -> list[dict[str, Any]]:
    return client(ctx).search(query, limit=limit)


@tool("Show an X post")
def post(ctx: ToolContext, post_id: str) -> dict[str, Any]:
    return client(ctx).post(post_id)


@tool("Show an X account")
def user(ctx: ToolContext, username: str) -> dict[str, Any]:
    return client(ctx).user(username)


@tool("List posts from an X account")
def timeline(
    ctx: ToolContext,
    username: str | None = None,
    user_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    return client(ctx).timeline(username=username, user_id=user_id, limit=limit)

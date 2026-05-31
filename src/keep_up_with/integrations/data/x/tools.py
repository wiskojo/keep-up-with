from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.x.client import XClient


def client(ctx: ToolContext) -> XClient:
    return XClient(ctx.env("X_BEARER_TOKEN"))


@tool("Search recent X posts.")
def search(ctx: ToolContext, query: str, limit: int = 10) -> list[dict[str, Any]]:
    return client(ctx).search(query, limit=limit)


@tool("Fetch a single X post.")
def post(ctx: ToolContext, post_id: str) -> dict[str, Any]:
    return client(ctx).post(post_id)


@tool("Fetch an X user by username.")
def user(ctx: ToolContext, username: str) -> dict[str, Any]:
    return client(ctx).user(username)


@tool("List recent posts from an X user.")
def timeline(
    ctx: ToolContext,
    username: str | None = None,
    user_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    return client(ctx).timeline(username=username, user_id=user_id, limit=limit)

from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import resolve_path
from keep_up_with.integrations.data.x.client import XClient


def client(ctx: ToolContext) -> XClient:
    return XClient(ctx.env("X_BEARER_TOKEN"))


@tool("Search X posts")
def search(ctx: ToolContext, query: str, limit: int = 10) -> list[dict[str, Any]]:
    return client(ctx).search(query, limit=limit)


@tool("Download an X post")
def download(
    ctx: ToolContext,
    post_id: str,
    output_dir: str,
    include_thread: bool = True,
) -> dict[str, Any]:
    return client(ctx).download(
        post_id,
        output_dir=resolve_path(output_dir),
        include_thread=include_thread,
    )


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

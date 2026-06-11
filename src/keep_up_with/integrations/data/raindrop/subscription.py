from __future__ import annotations

from keep_up_with.integrations.base import SubscriptionContext, poll_every
from keep_up_with.integrations.data.raindrop import client


@poll_every("raindrop.bookmarks", default_interval_seconds=300)
def bookmarks(ctx: SubscriptionContext) -> None:
    settings = ctx.settings()
    for item in client.bookmarks(
        ctx.env("RAINDROP_TOKEN"),
        since=str(settings.get("since") or "PT10M"),
        limit=int(settings.get("limit") or 200),
    ):
        key = f"{item.get('created_at', '')}:{item.get('url', '')}"
        ctx.emit(
            kind="bookmark",
            external_id=key,
            summary=f"Raindrop: {item.get('title') or item.get('url') or 'Bookmark'}",
            refs={"url": item.get("url", "")},
            data=item,
        )

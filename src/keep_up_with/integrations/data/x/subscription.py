from __future__ import annotations

from keep_up_with.integrations.base import SubscriptionContext, poll_every
from keep_up_with.integrations.data.x.client import XClient


@poll_every("x.posts", default_interval_seconds=300)
def posts(ctx: SubscriptionContext) -> None:
    settings = ctx.settings()
    accounts = [
        str(item).removeprefix("@").strip()
        for item in settings.get("accounts") or []
        if str(item).strip()
    ]
    if not accounts:
        return
    client = XClient(ctx.env("X_BEARER_TOKEN"))
    limit = int(settings.get("limit") or 10)
    for account in accounts:
        for item in client.timeline(username=account, limit=limit):
            post_id = item.get("id")
            if not post_id:
                continue
            author = item.get("author") if isinstance(item.get("author"), dict) else {}
            username = author.get("username") or account
            ctx.emit(
                kind="post",
                external_id=str(post_id),
                summary=f"@{username}: {item.get('text') or 'post'}",
                refs={"post_id": post_id, "url": item.get("url", "")},
                data=item,
            )

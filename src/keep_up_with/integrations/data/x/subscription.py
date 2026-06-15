from __future__ import annotations

from keep_up_with.integrations.base import SubscriptionContext, subscription
from keep_up_with.integrations.data.x.client import XClient, author_display, clean_accounts


@subscription("x.posts")
def posts(ctx: SubscriptionContext) -> None:
    settings = ctx.settings()
    accounts = clean_accounts(settings.get("accounts") or [])
    if not accounts:
        while not ctx.should_stop():
            ctx.wait(60)
        return

    client = XClient(ctx.env("X_BEARER_TOKEN"))
    for item in client.stream_accounts(accounts, should_stop=ctx.should_stop):
        post_id = item.get("id")
        if not post_id:
            continue
        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        ctx.emit(
            kind="post",
            external_id=str(post_id),
            summary=(
                f"{author_display(author, fallback=str(item.get('author_id') or ''))}: "
                f"{item.get('text') or 'post'}"
            ),
            summary_limit=1200,
            refs={"post_id": post_id, "url": item.get("url", "")},
            data=item,
        )

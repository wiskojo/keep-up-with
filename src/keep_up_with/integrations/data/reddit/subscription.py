from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from keep_up_with.integrations.base import SubscriptionContext, poll_every
from keep_up_with.integrations.data.reddit.client import RedditClient

WATCHES = (("hot", "all"), ("top", "day"))


@poll_every("reddit.posts", default_interval_seconds=3600)
def posts(ctx: SubscriptionContext) -> None:
    settings = ctx.settings()
    subreddits = [str(item) for item in settings.get("subreddits") or [] if str(item).strip()]
    limit = int(settings.get("limit") or 25)
    window_hours = int(settings.get("window_hours") or 24)
    client = RedditClient(
        client_id=ctx.env("REDDIT_CLIENT_ID"),
        client_secret=ctx.env("REDDIT_CLIENT_SECRET"),
    )

    for subreddit in subreddits:
        seen: set[str] = set()
        for sort, period in WATCHES:
            for item in client.posts(subreddit, sort=sort, period=period, limit=limit):
                item_id = str(
                    item.get("id") or item.get("name") or item.get("permalink") or ""
                )
                if (
                    not item_id
                    or item_id in seen
                    or not _within_window(item.get("created_at"), window_hours)
                ):
                    continue
                seen.add(item_id)
                item["watch_subreddit"] = subreddit
                item["watch_sort"] = "hot+top/day"
                item["watch_period"] = f"{window_hours}h"
                actor = f"r/{item.get('subreddit') or subreddit}"
                ctx.emit(
                    kind="headline",
                    external_id=item_id,
                    summary=post_summary(actor, item),
                    refs={
                        "post_id": item.get("id", ""),
                        "url": item.get("permalink") or item.get("url") or "",
                    },
                    data=item,
                )


def post_summary(actor: str, item: dict[str, Any]) -> str:
    title = item.get("title") or "New post"
    metrics = post_metrics(item)
    suffix = f" ({metrics})" if metrics else ""
    return f"{actor}: {title}{suffix}"


def post_metrics(item: dict[str, Any]) -> str:
    parts: list[str] = []
    score = metric_value(item.get("score"))
    comments = metric_value(item.get("num_comments"))
    if score is not None:
        parts.append(plural(score, "upvote"))
    if comments is not None:
        parts.append(plural(comments, "comment"))
    return ", ".join(parts)


def metric_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def plural(value: int, noun: str) -> str:
    suffix = "" if value == 1 else "s"
    return f"{value:,} {noun}{suffix}"


def _within_window(value: Any, hours: int) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        created = datetime.fromisoformat(value)
    except ValueError:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created >= datetime.now(timezone.utc) - timedelta(hours=hours)

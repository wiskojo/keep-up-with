from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import praw

USER_AGENT = "script:keep-up-with:v0.1"


class RedditClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
    ) -> None:
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=USER_AGENT,
        )
        self.reddit.read_only = True

    def posts(
        self,
        subreddit: str,
        *,
        sort: str = "hot",
        period: str = "day",
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        source = self.reddit.subreddit(clean_subreddit(subreddit))
        sort = sort.lower()
        limit = clamp(limit, 1, 100)
        if sort == "hot":
            rows = source.hot(limit=limit)
        elif sort == "new":
            rows = source.new(limit=limit)
        elif sort == "top":
            rows = source.top(time_filter=period, limit=limit)
        elif sort == "rising":
            rows = source.rising(limit=limit)
        elif sort == "controversial":
            rows = source.controversial(time_filter=period, limit=limit)
        else:
            raise ValueError("sort must be hot, new, top, rising, or controversial")
        return [post_data(post) for post in rows]

    def search(
        self,
        query: str,
        *,
        subreddit: str | None = None,
        sort: str = "relevance",
        period: str = "all",
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        sort = sort.lower()
        if sort not in {"relevance", "hot", "top", "new", "comments"}:
            raise ValueError("sort must be relevance, hot, top, new, or comments")
        source = (
            self.reddit.subreddit(clean_subreddit(subreddit))
            if subreddit
            else self.reddit.subreddit("all")
        )
        return [
            post_data(post)
            for post in source.search(
                query,
                sort=sort,
                time_filter=period,
                limit=clamp(limit, 1, 100),
            )
        ]

    def thread(
        self,
        url_or_id: str,
        *,
        sort: str = "best",
        depth: int = 3,
        limit: int = 100,
    ) -> dict[str, Any]:
        post = self.reddit.submission(id=parse_thread_id(url_or_id))
        post.comment_sort = sort
        post.comments.replace_more(limit=0)
        remaining = [clamp(limit, 1, 500)]
        return {
            "post": post_data(post),
            "comments": comments(
                post.comments,
                depth=clamp(depth, 1, 10),
                remaining=remaining,
            ),
            "more": [],
        }


def post_data(post: Any) -> dict[str, Any]:
    return {
        "id": post.id or "",
        "name": post.name or f"t3_{post.id}",
        "subreddit": str(post.subreddit) if post.subreddit else "",
        "title": post.title or "",
        "author": str(post.author) if post.author else "",
        "score": post.score,
        "upvote_ratio": post.upvote_ratio,
        "num_comments": post.num_comments,
        "created_at": timestamp(post.created_utc),
        "created_utc": post.created_utc,
        "url": post.url or "",
        "permalink": f"https://reddit.com{post.permalink}",
        "selftext": post.selftext or "",
        "is_self": bool(post.is_self),
        "over_18": bool(post.over_18),
        "link_flair_text": post.link_flair_text or "",
        "spoiler": bool(post.spoiler),
        "stickied": bool(post.stickied),
    }


def comments(items: Any, *, depth: int, remaining: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if depth <= 0 or remaining[0] <= 0:
        return rows
    for item in items:
        if remaining[0] <= 0:
            break
        remaining[0] -= 1
        rows.append(
            {
                "type": "comment",
                "id": item.id or "",
                "author": str(item.author) if item.author else "",
                "score": item.score,
                "created_at": timestamp(item.created_utc),
                "created_utc": item.created_utc,
                "body": item.body or "",
                "permalink": f"https://reddit.com{item.permalink}",
                "replies": comments(item.replies, depth=depth - 1, remaining=remaining),
                "more": [],
            }
        )
    return rows


def parse_thread_id(value: str) -> str:
    value = value.strip()
    if "/" not in value:
        return value
    parsed = urlparse(value)
    parts = parsed.path.strip("/").split("/")
    if parsed.netloc.endswith("redd.it") and parts and parts[0]:
        return parts[0]
    try:
        return parts[parts.index("comments") + 1]
    except (ValueError, IndexError) as error:
        raise ValueError("expected a Reddit thread URL or post id") from error


def clean_subreddit(value: str | None) -> str:
    return (value or "").strip().removeprefix("r/").strip("/")


def timestamp(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))

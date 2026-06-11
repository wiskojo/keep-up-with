from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
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
            "post": post_data(post, include_media=True),
            "comments": comments(
                post.comments,
                depth=clamp(depth, 1, 10),
                remaining=remaining,
            ),
            "more": [],
        }


def post_data(post: Any, *, include_media: bool = False) -> dict[str, Any]:
    row = {
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
    if include_media:
        row["media"] = post_media(post)
    return row


def post_media(post: Any) -> list[dict[str, Any]]:
    media: list[dict[str, Any]] = []
    seen: set[str] = set()

    add_direct_url(media, seen, getattr(post, "url", ""), source="url")
    add_preview(media, seen, getattr(post, "preview", None))
    add_gallery(
        media,
        seen,
        getattr(post, "gallery_data", None),
        getattr(post, "media_metadata", None),
    )
    add_reddit_video(media, seen, getattr(post, "media", None), source="media")
    add_reddit_video(
        media,
        seen,
        getattr(post, "secure_media", None),
        source="secure_media",
    )
    add_thumbnail(media, seen, post)

    return media


def add_direct_url(
    rows: list[dict[str, Any]],
    seen: set[str],
    value: str,
    *,
    source: str,
) -> None:
    url = clean_url(value)
    if not url or not looks_like_media_url(url):
        return
    add_media(rows, seen, source=source, media_type=media_type_from_url(url), url=url)


def add_preview(
    rows: list[dict[str, Any]],
    seen: set[str],
    preview: Any,
) -> None:
    if not isinstance(preview, dict):
        return
    for image in preview.get("images") or []:
        if not isinstance(image, dict):
            continue
        source = image.get("source") or {}
        if isinstance(source, dict):
            add_media(
                rows,
                seen,
                source="preview",
                media_type="image",
                url=clean_url(source.get("url", "")),
                width=source.get("width"),
                height=source.get("height"),
            )
        variants = image.get("variants") or {}
        if isinstance(variants, dict):
            for variant_type, variant in variants.items():
                if not isinstance(variant, dict):
                    continue
                source = variant.get("source") or {}
                if not isinstance(source, dict):
                    continue
                add_media(
                    rows,
                    seen,
                    source=f"preview.{variant_type}",
                    media_type=variant_type,
                    url=clean_url(source.get("url", "")),
                    width=source.get("width"),
                    height=source.get("height"),
                )


def add_gallery(
    rows: list[dict[str, Any]],
    seen: set[str],
    gallery_data: Any,
    media_metadata: Any,
) -> None:
    if not isinstance(gallery_data, dict) or not isinstance(media_metadata, dict):
        return
    for item in gallery_data.get("items") or []:
        if not isinstance(item, dict):
            continue
        media_id = item.get("media_id")
        metadata = media_metadata.get(media_id)
        if not isinstance(metadata, dict):
            continue
        source = metadata.get("s") or {}
        if not isinstance(source, dict):
            continue
        url = clean_url(source.get("u") or source.get("gif") or source.get("mp4") or "")
        add_media(
            rows,
            seen,
            source="gallery",
            media_type=media_type_from_metadata(metadata),
            url=url,
            width=source.get("x"),
            height=source.get("y"),
            media_id=media_id,
        )


def add_reddit_video(
    rows: list[dict[str, Any]],
    seen: set[str],
    media: Any,
    *,
    source: str,
) -> None:
    if not isinstance(media, dict):
        return
    video = media.get("reddit_video") or {}
    if not isinstance(video, dict):
        return
    for key in ("fallback_url", "hls_url", "dash_url"):
        add_media(
            rows,
            seen,
            source=f"{source}.reddit_video",
            media_type="video",
            url=clean_url(video.get(key, "")),
            width=video.get("width"),
            height=video.get("height"),
            duration=video.get("duration"),
        )


def add_thumbnail(rows: list[dict[str, Any]], seen: set[str], post: Any) -> None:
    thumbnail = clean_url(getattr(post, "thumbnail", ""))
    if not thumbnail.startswith(("http://", "https://")):
        return
    add_media(
        rows,
        seen,
        source="thumbnail",
        media_type="thumbnail",
        url=thumbnail,
        width=getattr(post, "thumbnail_width", None),
        height=getattr(post, "thumbnail_height", None),
    )


def add_media(
    rows: list[dict[str, Any]],
    seen: set[str],
    *,
    source: str,
    media_type: str,
    url: str,
    width: Any = None,
    height: Any = None,
    duration: Any = None,
    media_id: Any = None,
) -> None:
    if not url or url in seen:
        return
    seen.add(url)
    item: dict[str, Any] = {"source": source, "type": media_type, "url": url}
    if width is not None:
        item["width"] = width
    if height is not None:
        item["height"] = height
    if duration is not None:
        item["duration"] = duration
    if media_id is not None:
        item["media_id"] = media_id
    rows.append(item)


def clean_url(value: Any) -> str:
    return unescape(str(value or "")).strip()


def looks_like_media_url(value: str) -> bool:
    parsed = urlparse(value)
    suffix = parsed.path.rsplit(".", 1)[-1].lower() if "." in parsed.path else ""
    return parsed.netloc.endswith(("redd.it", "redditmedia.com")) or suffix in {
        "apng",
        "avif",
        "gif",
        "jpeg",
        "jpg",
        "m4v",
        "mov",
        "mp4",
        "png",
        "svg",
        "webp",
        "webm",
    }


def media_type_from_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.netloc.startswith("v.redd.it"):
        return "video"
    suffix = parsed.path.rsplit(".", 1)[-1].lower()
    if suffix in {"m4v", "mov", "mp4", "webm"}:
        return "video"
    if suffix == "gif":
        return "gif"
    return "image"


def media_type_from_metadata(metadata: dict[str, Any]) -> str:
    media_type = str(metadata.get("e") or metadata.get("m") or "")
    if "video" in media_type:
        return "video"
    if "gif" in media_type:
        return "gif"
    return "image"


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

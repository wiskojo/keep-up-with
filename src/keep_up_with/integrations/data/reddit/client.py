from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import praw

USER_AGENT = "script:keep-up-with:v0.1"
MEDIA_URL_RE = re.compile(r"https?://[^\s)\]>]+")


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
            check_for_updates=False,
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
        depth: int = 1,
        limit: int = 20,
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

    def download(
        self,
        url_or_id: str,
        *,
        output_dir: Path,
        sort: str = "best",
        depth: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        data = self.thread(url_or_id, sort=sort, depth=depth, limit=limit)
        post = data["post"]
        target_dir = output_dir / f"reddit-thread-{safe_path_part(str(post['id']))}"
        media_dir = target_dir / "media"
        target_dir.mkdir(parents=True, exist_ok=True)

        json_path = target_dir / "thread.json"
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        media_results = download_media(collect_thread_media(data), media_dir)
        markdown_path = target_dir / "thread.md"
        markdown = thread_markdown(data, media_results, base_dir=target_dir)
        markdown_path.write_text(markdown, encoding="utf-8")
        return {
            "id": post["id"],
            "type": "reddit_thread",
            "directory": str(target_dir),
            "json": {"ok": True, "path": str(json_path)},
            "markdown": {
                "ok": True,
                "path": str(markdown_path),
                "characters": len(markdown),
            },
            "media": media_artifact(media_dir, media_results),
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

    return dedupe_media(media)


def comment_media(comment: Any) -> list[dict[str, Any]]:
    media: list[dict[str, Any]] = []
    seen: set[str] = set()
    add_body_media(media, seen, getattr(comment, "body", ""))
    add_media_metadata(
        media,
        seen,
        getattr(comment, "media_metadata", None),
        source="comment.media_metadata",
    )
    return dedupe_media(media)


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


def add_media_metadata(
    rows: list[dict[str, Any]],
    seen: set[str],
    media_metadata: Any,
    *,
    source: str,
) -> None:
    if not isinstance(media_metadata, dict):
        return
    for media_id, metadata in media_metadata.items():
        if not isinstance(metadata, dict):
            continue
        item = metadata.get("s") or {}
        if not isinstance(item, dict):
            continue
        url = clean_url(item.get("u") or item.get("gif") or item.get("mp4") or "")
        add_media(
            rows,
            seen,
            source=source,
            media_type=media_type_from_metadata(metadata),
            url=url,
            width=item.get("x"),
            height=item.get("y"),
            media_id=media_id,
        )


def add_body_media(rows: list[dict[str, Any]], seen: set[str], body: str) -> None:
    for match in MEDIA_URL_RE.finditer(body or ""):
        url = clean_url(match.group(0).rstrip(".,"))
        if not looks_like_media_url(url):
            continue
        add_media(
            rows,
            seen,
            source="comment.body",
            media_type=media_type_from_url(url),
            url=url,
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
    add_media(
        rows,
        seen,
        source=f"{source}.reddit_video",
        media_type="video",
        url=clean_url(video.get("fallback_url", "")),
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


def dedupe_media(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in rows:
        key = media_group_key(item)
        current = grouped.get(key)
        if current is None or media_quality(item) > media_quality(current):
            grouped[key] = item
    return list(grouped.values())


def media_group_key(item: dict[str, Any]) -> str:
    media_id = item.get("media_id")
    if media_id:
        return f"id:{media_id}"
    parsed = urlparse(str(item.get("url") or ""))
    stem = Path(parsed.path).stem
    if parsed.netloc.endswith(("redd.it", "redditmedia.com")) and stem:
        return f"reddit:{stem}"
    return f"url:{parsed.scheme}://{parsed.netloc}{parsed.path}"


def media_quality(item: dict[str, Any]) -> int:
    width = int(item.get("width") or 0)
    height = int(item.get("height") or 0)
    source = item.get("source") or ""
    media_type = item.get("type") or ""
    score = width * height
    if media_type != "thumbnail":
        score += 1_000_000_000
    if source in {"url", "gallery", "comment.media_metadata", "comment.body"}:
        score += 100_000_000
    if source.startswith("preview"):
        score += 10_000_000
    return score


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
                "media": comment_media(item),
                "replies": comments(item.replies, depth=depth - 1, remaining=remaining),
                "more": [],
            }
        )
    return rows


def thread_markdown(
    data: dict[str, Any],
    media_results: list[dict[str, Any]],
    *,
    base_dir: Path,
) -> str:
    post = data["post"]
    media_by_owner = group_media_results(media_results)
    lines = [
        f"# r/{post.get('subreddit')}: {post.get('title')}",
        "",
        f"Author: u/{post.get('author') or '[deleted]'}",
        f"Score: {post.get('score')}",
        f"Comments: {post.get('num_comments')}",
        f"Posted: {post.get('created_at')}",
        f"Permalink: {post.get('permalink')}",
        f"URL: {post.get('url')}",
        "",
    ]
    selftext = str(post.get("selftext") or "").strip()
    if selftext:
        lines.extend(["## Post", "", selftext, ""])
    media_rows = media_by_owner.get(("post", str(post.get("id") or "")), [])
    if media_rows:
        lines.extend(
            media_markdown_lines(
                media_rows,
                alt="Reddit post media",
                base_dir=base_dir,
            )
        )
    comments_data = data.get("comments") or []
    if comments_data:
        lines.extend(["## Comments", ""])
        for index, comment in enumerate(comments_data, start=1):
            append_comment_markdown(
                lines,
                comment,
                prefix=f"{index}.",
                media_by_owner=media_by_owner,
                base_dir=base_dir,
            )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def append_comment_markdown(
    lines: list[str],
    comment: dict[str, Any],
    *,
    prefix: str,
    media_by_owner: dict[tuple[str, str], list[dict[str, Any]]],
    base_dir: Path,
    indent: int = 0,
) -> None:
    pad = "  " * indent
    author = comment.get("author") or "[deleted]"
    score = comment.get("score")
    permalink = comment.get("permalink") or ""
    lines.append(f"{pad}{prefix} u/{author} · {score} points")
    if permalink:
        lines.append(f"{pad}   {permalink}")
    body = str(comment.get("body") or "").strip()
    if body:
        for line in body.splitlines():
            quote = line.strip()
            lines.append(f"{pad}   > {quote}" if quote else f"{pad}   >")
    media_rows = media_by_owner.get(("comment", str(comment.get("id") or "")), [])
    if media_rows:
        for item in media_rows:
            lines.extend(
                f"{pad}   {line}" if line else ""
                for line in media_markdown_lines(
                    [item],
                    alt=f"Reddit comment {comment.get('id') or ''} media",
                    base_dir=base_dir,
                )
            )
    for reply_index, reply in enumerate(comment.get("replies") or [], start=1):
        append_comment_markdown(
            lines,
            reply,
            prefix=f"{prefix}{reply_index}.",
            media_by_owner=media_by_owner,
            base_dir=base_dir,
            indent=indent + 1,
        )


def collect_thread_media(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    post = data.get("post") or {}
    for item in post.get("media") or []:
        rows.append(
            {
                **item,
                "owner_type": "post",
                "owner_id": str(post.get("id") or ""),
            }
        )

    def collect_comments(comments_data: list[dict[str, Any]]) -> None:
        for comment in comments_data:
            for item in comment.get("media") or []:
                rows.append(
                    {
                        **item,
                        "owner_type": "comment",
                        "owner_id": str(comment.get("id") or ""),
                    }
                )
            collect_comments(comment.get("replies") or [])

    collect_comments(data.get("comments") or [])
    return rows


def media_markdown_lines(
    rows: list[dict[str, Any]],
    *,
    alt: str,
    base_dir: Path,
) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(rows, start=1):
        label = media_markdown_target(item, base_dir=base_dir)
        if not label:
            continue
        if item.get("ok"):
            lines.extend(["", f"![{alt} {index}]({label})"])
            continue
        status = item.get("error") or "download failed"
        lines.extend(["", f"- {label} ({status})"])
    if lines:
        lines.append("")
    return lines


def media_markdown_target(item: dict[str, Any], *, base_dir: Path) -> str:
    path = item.get("path") or ""
    if path:
        try:
            return Path(path).relative_to(base_dir).as_posix()
        except ValueError:
            return str(path)
    return str(item.get("url") or "")


def download_media(rows: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        suffix = url_suffix(url, default=".bin")
        media_id = item.get("media_id") or f"media-{index:02d}"
        path = output_dir / f"{safe_path_part(str(media_id))}{suffix}"
        result = {
            "owner_type": item.get("owner_type") or "",
            "owner_id": item.get("owner_id") or "",
            "url": url,
            "type": item.get("type") or "",
            "source": item.get("source") or "",
            "path": str(path),
        }
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            download_file(url, path)
            result["ok"] = True
        except Exception as error:
            result["ok"] = False
            result["error"] = f"{type(error).__name__}: {error}"
        results.append(result)
    return results


def group_media_results(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in rows:
        key = (str(item.get("owner_type") or ""), str(item.get("owner_id") or ""))
        grouped.setdefault(key, []).append(item)
    return grouped


def media_artifact(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [
        {"url": item.get("url", ""), "error": item.get("error", "")}
        for item in rows
        if not item.get("ok")
    ]
    return {
        "ok": not errors,
        "directory": str(output_dir),
        "files": [item["path"] for item in rows if item.get("ok") and item.get("path")],
        "errors": errors,
    }


def download_file(url: str, path: Path) -> None:
    with httpx.stream("GET", url, timeout=60, follow_redirects=True) as response:
        response.raise_for_status()
        with path.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)


def url_suffix(url: str, *, default: str) -> str:
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix else default


def safe_path_part(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-._" else "-" for char in value)
    return cleaned.strip(".-") or "item"


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

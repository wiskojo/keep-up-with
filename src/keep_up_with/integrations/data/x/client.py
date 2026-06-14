from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

BASE_URL = "https://api.x.com"
POST_FIELDS = (
    "attachments,author_id,created_at,conversation_id,lang,note_tweet,public_metrics,"
    "referenced_tweets"
)
USER_FIELDS = "created_at,description,public_metrics,verified,verified_type"
EXPANSIONS = "author_id"
POST_EXPANSIONS = "author_id,attachments.media_keys"
DOWNLOAD_POST_FIELDS = f"article,entities,{POST_FIELDS}"
DOWNLOAD_POST_EXPANSIONS = (
    "author_id,attachments.media_keys,article.cover_media,article.media_entities"
)
MEDIA_FIELDS = (
    "alt_text,duration_ms,height,media_key,preview_image_url,public_metrics,type,url,"
    "variants,width"
)
STREAM_RULE_TAG_PREFIX = "keep-up-with:x.posts"
STREAM_RULE_MAX_LENGTH = 1024
STREAM_READ_TIMEOUT_SECONDS = 30.0


class XClient:
    def __init__(self, bearer_token: str) -> None:
        self.bearer_token = bearer_token

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        requested = clamp(limit, 1, 100)
        return posts(
            self.get(
                "/2/tweets/search/recent",
                {
                    "query": query,
                    "max_results": clamp(requested, 10, 100),
                    "tweet.fields": POST_FIELDS,
                    "user.fields": USER_FIELDS,
                    "expansions": EXPANSIONS,
                },
            )
        )[:requested]

    def post(self, post_id: str) -> dict[str, Any]:
        clean_id = post_id.rstrip("/").split("/")[-1].split("?", 1)[0]
        rows = posts(
            self.get(
                f"/2/tweets/{clean_id}",
                {
                    "tweet.fields": DOWNLOAD_POST_FIELDS,
                    "user.fields": USER_FIELDS,
                    "media.fields": MEDIA_FIELDS,
                    "expansions": DOWNLOAD_POST_EXPANSIONS,
                },
            ),
            include_media=True,
        )
        return rows[0] if rows else {}

    def download(
        self,
        post_id: str,
        *,
        output_dir: Path,
        include_thread: bool = True,
    ) -> dict[str, Any]:
        post = self.post(post_id)
        if not post:
            raise ValueError(f"unknown X post: {post_id}")

        thread_posts = [post]
        thread_error = ""
        if include_thread:
            try:
                thread_posts = self.self_thread(post) or [post]
            except Exception as error:
                thread_error = f"{type(error).__name__}: {error}"

        target_dir = output_dir / f"x-post-{safe_path_part(str(post['id']))}"
        media_dir = target_dir / "media"
        target_dir.mkdir(parents=True, exist_ok=True)

        json_path = target_dir / "post.json"
        json_payload: dict[str, Any] = {"posts": thread_posts}
        if thread_error:
            json_payload["thread_error"] = thread_error
        json_path.write_text(
            json.dumps(json_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        media_results = download_media(thread_posts, media_dir)
        markdown_path = target_dir / "post.md"
        markdown = post_markdown(
            thread_posts,
            media_results,
            base_dir=target_dir,
            thread_error=thread_error,
        )
        markdown_path.write_text(markdown, encoding="utf-8")
        return {
            "id": post["id"],
            "type": "x_post",
            "directory": str(target_dir),
            "json": {"ok": True, "path": str(json_path)},
            "markdown": {
                "ok": True,
                "path": str(markdown_path),
                "characters": len(markdown),
            },
            "media": media_artifact(media_dir, media_results),
        }

    def self_thread(self, post: dict[str, Any]) -> list[dict[str, Any]]:
        conversation_id = post.get("conversation_id") or post.get("id") or ""
        author_id = post.get("author_id") or ""
        if not conversation_id or not author_id:
            return [post]
        endpoint = x_search_endpoint_for_post(post)
        rows = posts(
            self.get(
                endpoint,
                {
                    "query": f"conversation_id:{conversation_id} from:{author_id} -is:retweet",
                    "max_results": 100,
                    "tweet.fields": DOWNLOAD_POST_FIELDS,
                    "user.fields": USER_FIELDS,
                    "media.fields": MEDIA_FIELDS,
                    "expansions": DOWNLOAD_POST_EXPANSIONS,
                },
            ),
            include_media=True,
        )
        if not rows:
            return [post]
        by_id = {row["id"]: row for row in rows}
        by_id.setdefault(str(post["id"]), post)
        return prune_self_thread(
            list(by_id.values()),
            root_id=str(conversation_id),
        )

    def user(self, username: str) -> dict[str, Any]:
        data = self.get(
            f"/2/users/by/username/{username.removeprefix('@')}",
            {"user.fields": USER_FIELDS},
        ).get("data")
        return user(data) if isinstance(data, dict) else {}

    def timeline(
        self,
        *,
        username: str | None = None,
        user_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if user_id is None:
            if username is None:
                raise ValueError("username or user_id is required")
            user_id = self.user(username).get("id")
        if not user_id:
            return []
        requested = clamp(limit, 1, 100)
        return posts(
            self.get(
                f"/2/users/{user_id}/tweets",
                {
                    "max_results": clamp(requested, 5, 100),
                    "tweet.fields": POST_FIELDS,
                    "user.fields": USER_FIELDS,
                    "expansions": EXPANSIONS,
                },
            )
        )[:requested]

    def stream_accounts(
        self,
        accounts: Iterable[str],
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[dict[str, Any]]:
        account_list = clean_accounts(accounts)
        self.sync_account_stream_rules(account_list)
        if not account_list:
            return
        yield from self.filtered_stream(should_stop=should_stop)

    def sync_account_stream_rules(self, accounts: Iterable[str]) -> None:
        desired_values = account_stream_rule_values(accounts)
        desired_by_value = {
            value: f"{STREAM_RULE_TAG_PREFIX}:{index}"
            for index, value in enumerate(desired_values)
        }
        managed_rules = [
            rule
            for rule in self.stream_rules()
            if str(rule.get("tag") or "").startswith(STREAM_RULE_TAG_PREFIX)
        ]

        delete_ids = [
            str(rule.get("id"))
            for rule in managed_rules
            if rule.get("id") and rule.get("value") not in desired_by_value
        ]
        add_rules = [
            {"value": value, "tag": tag}
            for value, tag in desired_by_value.items()
            if value not in {rule.get("value") for rule in managed_rules}
        ]

        if delete_ids:
            self.post_json(
                "/2/tweets/search/stream/rules",
                {"delete": {"ids": delete_ids}},
            )
        if add_rules:
            self.post_json("/2/tweets/search/stream/rules", {"add": add_rules})

    def stream_rules(self) -> list[dict[str, Any]]:
        rules: list[dict[str, Any]] = []
        next_token: str | None = None
        while True:
            params: dict[str, Any] = {"max_results": 1000}
            if next_token:
                params["pagination_token"] = next_token
            payload = self.get("/2/tweets/search/stream/rules", params)
            rules.extend(
                rule for rule in payload.get("data", []) if isinstance(rule, dict)
            )
            token = payload.get("meta", {}).get("next_token")
            if not token:
                return rules
            next_token = str(token)

    def filtered_stream(
        self,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[dict[str, Any]]:
        params = {
            "tweet.fields": POST_FIELDS,
            "user.fields": USER_FIELDS,
            "expansions": EXPANSIONS,
        }
        timeout = httpx.Timeout(30.0, read=STREAM_READ_TIMEOUT_SECONDS)
        with httpx.stream(
            "GET",
            f"{BASE_URL}/2/tweets/search/stream",
            params=params,
            headers=self.headers(),
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if should_stop and should_stop():
                    return
                if not line:
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    continue
                matching_rules = payload.get("matching_rules") or []
                for row in posts(payload):
                    row["matching_rules"] = matching_rules
                    yield row

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = httpx.get(
            f"{BASE_URL}{path}",
            params=params,
            headers=self.headers(),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}

    def post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{BASE_URL}{path}",
            json=body,
            headers=self.headers(),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}


def x_search_endpoint_for_post(post: dict[str, Any]) -> str:
    created = datetime.fromisoformat(str(post["created_at"]).replace("Z", "+00:00"))
    if datetime.now(timezone.utc) - created >= timedelta(days=6):
        return "/2/tweets/search/all"
    return "/2/tweets/search/recent"


def clean_accounts(accounts: Iterable[str]) -> list[str]:
    clean: list[str] = []
    seen: set[str] = set()
    for account in accounts:
        username = str(account).removeprefix("@").strip()
        key = username.lower()
        if not username or key in seen:
            continue
        clean.append(username)
        seen.add(key)
    return clean


def account_stream_rule_values(accounts: Iterable[str]) -> list[str]:
    rules: list[str] = []
    current_terms: list[str] = []
    for account in clean_accounts(accounts):
        term = f"from:{account}"
        candidate_terms = [*current_terms, term]
        candidate = account_stream_rule_value(candidate_terms)
        if len(candidate) <= STREAM_RULE_MAX_LENGTH:
            current_terms = candidate_terms
            continue
        if not current_terms:
            raise ValueError(f"X stream rule is too long for account: {account}")
        rules.append(account_stream_rule_value(current_terms))
        current_terms = [term]
    if current_terms:
        rules.append(account_stream_rule_value(current_terms))
    return rules


def account_stream_rule_value(terms: list[str]) -> str:
    if len(terms) == 1:
        return terms[0]
    return f"({' OR '.join(terms)})"


def posts(data: dict[str, Any], *, include_media: bool = False) -> list[dict[str, Any]]:
    users = {
        item.get("id"): user(item)
        for item in data.get("includes", {}).get("users", [])
        if isinstance(item, dict)
    }
    media_by_key = {
        item.get("media_key"): media(item)
        for item in data.get("includes", {}).get("media", [])
        if isinstance(item, dict)
    }
    raw_posts = data.get("data") or []
    if isinstance(raw_posts, dict):
        raw_posts = [raw_posts]
    if not isinstance(raw_posts, list):
        return []

    rows = []
    for item in raw_posts:
        if not isinstance(item, dict):
            continue
        author = users.get(item.get("author_id"), {})
        row = {
            "id": item.get("id") or "",
            "text": post_text(item),
            "author_id": item.get("author_id") or "",
            "author": author,
            "created_at": item.get("created_at") or "",
            "conversation_id": item.get("conversation_id") or "",
            "lang": item.get("lang") or "",
            "metrics": item.get("public_metrics") or {},
            "referenced_tweets": item.get("referenced_tweets") or [],
            "url": post_url(author, item),
        }
        entities = item.get("entities") or {}
        if entities:
            row["entities"] = entities
        article = post_article(item, media_by_key)
        if article:
            row["article"] = article
        if include_media:
            row["media"] = post_media(item, media_by_key)
        rows.append(row)
    return rows


def post_text(post: dict[str, Any]) -> str:
    note = post.get("note_tweet")
    if isinstance(note, dict) and isinstance(note.get("text"), str):
        return unescape(note["text"])
    return unescape(post.get("text") or "")


def post_media(
    post: dict[str, Any],
    media_by_key: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    attachments = post.get("attachments") or {}
    if not isinstance(attachments, dict):
        return []
    keys = attachments.get("media_keys") or []
    if not isinstance(keys, list):
        return []
    return [
        media_by_key[key]
        for key in keys
        if isinstance(key, str) and key in media_by_key
    ]


def post_article(
    post: dict[str, Any],
    media_by_key: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw_article = post.get("article")
    if not isinstance(raw_article, dict):
        return {}
    return {
        "title": raw_article.get("title") or "",
        "plain_text": unescape(raw_article.get("plain_text") or ""),
        "preview_text": unescape(raw_article.get("preview_text") or ""),
        "entities": raw_article.get("entities") or {},
        "cover_media": raw_article.get("cover_media") or "",
        "media_entities": raw_article.get("media_entities") or [],
        "media": article_media(raw_article, media_by_key),
    }


def article_media(
    article: dict[str, Any],
    media_by_key: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    keys: list[str] = []
    cover_media = article.get("cover_media")
    if isinstance(cover_media, str):
        keys.append(cover_media)
    media_entities = article.get("media_entities") or []
    if isinstance(media_entities, list):
        keys.extend(key for key in media_entities if isinstance(key, str))
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for key in keys:
        if key in seen or key not in media_by_key:
            continue
        seen.add(key)
        rows.append(media_by_key[key])
    return rows


def media(data: dict[str, Any]) -> dict[str, Any]:
    raw_variants = data.get("variants") or []
    variants = [
        {
            "bit_rate": item.get("bit_rate"),
            "content_type": item.get("content_type") or "",
            "url": item.get("url") or "",
        }
        for item in raw_variants
        if isinstance(item, dict)
    ]
    return {
        "media_key": data.get("media_key") or "",
        "type": data.get("type") or "",
        "url": data.get("url") or "",
        "preview_image_url": data.get("preview_image_url") or "",
        "variants": variants,
        "alt_text": data.get("alt_text") or "",
        "width": data.get("width"),
        "height": data.get("height"),
        "duration_ms": data.get("duration_ms"),
        "metrics": data.get("public_metrics") or {},
    }


def user(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data.get("id") or "",
        "username": data.get("username") or "",
        "name": data.get("name") or "",
        "description": data.get("description") or "",
        "created_at": data.get("created_at") or "",
        "verified": data.get("verified") or False,
        "verified_type": data.get("verified_type") or "",
        "metrics": data.get("public_metrics") or {},
    }


def post_url(author: dict[str, Any], post: dict[str, Any]) -> str:
    username = author.get("username")
    post_id = post.get("id")
    if not username or not post_id:
        return ""
    return f"https://x.com/{username}/status/{post_id}"


def prune_self_thread(rows: list[dict[str, Any]], *, root_id: str) -> list[dict[str, Any]]:
    remaining = {str(row.get("id") or ""): row for row in rows if row.get("id")}
    kept_ids: set[str] = set()
    kept: dict[str, dict[str, Any]] = {}
    while True:
        changed = False
        for post_id, row in list(remaining.items()):
            if post_id == root_id or replied_to_kept_post(row, kept_ids):
                kept[post_id] = row
                kept_ids.add(post_id)
                del remaining[post_id]
                changed = True
        if not changed:
            break
    return sorted(kept.values(), key=post_sort_key)


def replied_to_kept_post(row: dict[str, Any], kept_ids: set[str]) -> bool:
    for reference in row.get("referenced_tweets") or []:
        if not isinstance(reference, dict):
            continue
        if reference.get("type") != "replied_to":
            continue
        if str(reference.get("id") or "") in kept_ids:
            return True
    return False


def post_sort_key(row: dict[str, Any]) -> tuple[str, int]:
    post_id = str(row.get("id") or "")
    try:
        id_value = int(post_id)
    except ValueError:
        id_value = 0
    return str(row.get("created_at") or ""), id_value


def post_markdown(
    rows: list[dict[str, Any]],
    media_results: list[dict[str, Any]],
    *,
    base_dir: Path,
    thread_error: str = "",
) -> str:
    lines: list[str] = []
    if thread_error:
        lines.extend([f"Thread expansion error: {thread_error}", ""])
    media_by_post = group_media_results(media_results)
    for index, row in enumerate(rows, start=1):
        author = row.get("author") or {}
        username = author.get("username") or row.get("author_id") or "unknown"
        metrics = row.get("metrics") or {}
        lines.extend(
            [
                f"## Post {index}",
                "",
                f"Author: @{username}",
                f"Posted: {row.get('created_at') or ''}",
                f"URL: {row.get('url') or ''}",
                f"Metrics: {post_metrics(metrics)}",
                "",
                str(row.get("text") or "").strip(),
                "",
            ]
        )
        lines.extend(quoted_post_markdown_lines(row))
        lines.extend(article_markdown_lines(row))
        media_rows = media_by_post.get(str(row.get("id") or ""), [])
        if media_rows:
            lines.extend(
                media_markdown_lines(
                    media_rows,
                    alt=f"X post {index} media",
                    base_dir=base_dir,
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def article_markdown_lines(row: dict[str, Any]) -> list[str]:
    article = row.get("article") or {}
    if not article:
        return []
    lines = ["Article:", ""]
    title = str(article.get("title") or "").strip()
    if title:
        lines.extend([f"### {title}", ""])
    text = str(article.get("plain_text") or "").strip()
    if text:
        lines.extend([text, ""])
    return lines


def quoted_post_markdown_lines(row: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for reference in row.get("referenced_tweets") or []:
        if not isinstance(reference, dict) or reference.get("type") != "quoted":
            continue
        post_id = str(reference.get("id") or "")
        if not post_id:
            continue
        lines.extend(["Quoted post:", "", f"> {x_status_url(post_id)}", ""])
    return lines


def x_status_url(post_id: str) -> str:
    return f"https://x.com/i/status/{post_id}"


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
            lines.append(f"![{alt} {index}]({label})")
            continue
        status = item.get("error") or "download failed"
        lines.append(f"- {label} ({status})")
    if lines:
        lines.append("")
    return lines


def post_metrics(metrics: dict[str, Any]) -> str:
    parts = [
        f"{metrics.get('reply_count', 0)} replies",
        f"{metrics.get('retweet_count', 0)} reposts",
        f"{metrics.get('like_count', 0)} likes",
        f"{metrics.get('quote_count', 0)} quotes",
    ]
    if "impression_count" in metrics:
        parts.append(f"{metrics.get('impression_count', 0)} impressions")
    return ", ".join(parts)


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
    counter = 1
    for row in rows:
        for item in row_media(row):
            if not isinstance(item, dict):
                continue
            candidate = media_download_candidate(item)
            url = candidate.get("url", "")
            if not url or url in seen:
                if item.get("type") in {"video", "animated_gif"} and row.get("url"):
                    result = download_video_with_ytdlp(
                        str(row["url"]),
                        output_dir=output_dir,
                        stem=safe_path_part(str(item.get("media_key") or f"media-{counter:02d}")),
                        post_id=str(row.get("id") or ""),
                        media_type=str(item.get("type") or ""),
                    )
                    counter += 1
                    results.append(result)
                continue
            seen.add(url)
            suffix = url_suffix(url, default=candidate.get("default_suffix", ".bin"))
            name = item.get("media_key") or f"media-{counter:02d}"
            counter += 1
            path = output_dir / f"{safe_path_part(str(name))}{suffix}"
            result = {
                "post_id": row.get("id") or "",
                "url": url,
                "type": item.get("type") or "",
                "source": candidate.get("source", ""),
                "path": str(path),
            }
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                download_file(url, path)
                result["ok"] = True
            except Exception as error:
                if item.get("type") in {"video", "animated_gif"} and row.get("url"):
                    result = download_video_with_ytdlp(
                        str(row["url"]),
                        output_dir=output_dir,
                        stem=safe_path_part(str(name)),
                        post_id=str(row.get("id") or ""),
                        media_type=str(item.get("type") or ""),
                        fallback_error=f"{type(error).__name__}: {error}",
                    )
                else:
                    result["ok"] = False
                    result["error"] = f"{type(error).__name__}: {error}"
            results.append(result)
    return results


def row_media(row: dict[str, Any]) -> list[dict[str, Any]]:
    media_rows = list(row.get("media") or [])
    article = row.get("article") or {}
    if isinstance(article, dict):
        media_rows.extend(article.get("media") or [])
    return media_rows


def media_download_candidate(item: dict[str, Any]) -> dict[str, str]:
    media_type = item.get("type") or ""
    if media_type in {"video", "animated_gif"}:
        variant = best_video_variant(item.get("variants") or [])
        if variant:
            return {
                "url": variant["url"],
                "source": "variant",
                "default_suffix": ".mp4",
            }
        return {"url": "", "source": "", "default_suffix": ".mp4"}
    url = item.get("url") or item.get("preview_image_url") or ""
    return {"url": url, "source": "url", "default_suffix": ".jpg"}


def best_video_variant(variants: list[dict[str, Any]]) -> dict[str, Any]:
    mp4s = [
        item
        for item in variants
        if item.get("url") and item.get("content_type") == "video/mp4"
    ]
    if not mp4s:
        return {}
    return max(mp4s, key=lambda item: int(item.get("bit_rate") or 0))


def download_video_with_ytdlp(
    url: str,
    *,
    output_dir: Path,
    stem: str,
    post_id: str,
    media_type: str,
    fallback_error: str = "",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    template = output_dir / f"{stem}.%(ext)s"
    try:
        from yt_dlp import YoutubeDL
    except ImportError as error:
        return {
            "post_id": post_id,
            "url": url,
            "type": media_type,
            "source": "yt-dlp",
            "path": "",
            "ok": False,
            "error": f"yt-dlp is required: {error}",
        }
    try:
        with YoutubeDL(
            {
                "quiet": True,
                "no_warnings": True,
                "outtmpl": str(template),
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            }
        ) as downloader:
            downloader.download([url])
    except Exception as error:
        detail = f"{type(error).__name__}: {error}"
        if fallback_error:
            detail = f"{fallback_error}; yt-dlp fallback failed: {detail}"
        return {
            "post_id": post_id,
            "url": url,
            "type": media_type,
            "source": "yt-dlp",
            "path": "",
            "ok": False,
            "error": detail,
        }
    files = sorted(output_dir.glob(f"{stem}.*"))
    path = files[0] if files else output_dir / f"{stem}.mp4"
    return {
        "post_id": post_id,
        "url": url,
        "type": media_type,
        "source": "yt-dlp",
        "path": str(path),
        "ok": path.exists(),
        **({} if path.exists() else {"error": "yt-dlp did not create an output file"}),
    }


def group_media_results(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("post_id") or ""), []).append(row)
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


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))

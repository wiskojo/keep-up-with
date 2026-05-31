from __future__ import annotations

from typing import Any

import httpx

POST_FIELDS = "author_id,created_at,conversation_id,lang,public_metrics,referenced_tweets"
USER_FIELDS = "created_at,description,public_metrics,verified,verified_type"
EXPANSIONS = "author_id"


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
                    "tweet.fields": POST_FIELDS,
                    "user.fields": USER_FIELDS,
                    "expansions": EXPANSIONS,
                },
            )
        )
        return rows[0] if rows else {}

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

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = httpx.get(
            f"https://api.x.com{path}",
            params=params,
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}


def posts(data: dict[str, Any]) -> list[dict[str, Any]]:
    users = {
        item.get("id"): user(item)
        for item in data.get("includes", {}).get("users", [])
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
        rows.append(
            {
                "id": item.get("id") or "",
                "text": item.get("text") or "",
                "author_id": item.get("author_id") or "",
                "author": author,
                "created_at": item.get("created_at") or "",
                "conversation_id": item.get("conversation_id") or "",
                "lang": item.get("lang") or "",
                "metrics": item.get("public_metrics") or {},
                "referenced_tweets": item.get("referenced_tweets") or [],
                "url": post_url(author, item),
            }
        )
    return rows


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


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))

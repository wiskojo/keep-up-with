from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator
from typing import Any

import httpx

BASE_URL = "https://api.x.com"
POST_FIELDS = (
    "attachments,author_id,created_at,conversation_id,lang,public_metrics,"
    "referenced_tweets"
)
USER_FIELDS = "created_at,description,public_metrics,verified,verified_type"
EXPANSIONS = "author_id"
POST_EXPANSIONS = "author_id,attachments.media_keys"
MEDIA_FIELDS = (
    "alt_text,duration_ms,height,media_key,preview_image_url,public_metrics,type,url,width"
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
                    "tweet.fields": POST_FIELDS,
                    "user.fields": USER_FIELDS,
                    "media.fields": MEDIA_FIELDS,
                    "expansions": POST_EXPANSIONS,
                },
            ),
            include_media=True,
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
        if include_media:
            row["media"] = post_media(item, media_by_key)
        rows.append(row)
    return rows


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


def media(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "media_key": data.get("media_key") or "",
        "type": data.get("type") or "",
        "url": data.get("url") or "",
        "preview_image_url": data.get("preview_image_url") or "",
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


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))

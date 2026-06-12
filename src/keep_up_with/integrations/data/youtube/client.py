from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

CHANNEL_CACHE: dict[str, str] = {}


def channel(api_key: str, channel: str, *, limit: int = 10) -> dict[str, Any]:
    channel_id = resolve_channel_id(api_key, channel)
    channel_data = youtube_get(
        api_key,
        "channels",
        {"part": "contentDetails,snippet,statistics", "id": channel_id, "maxResults": 1},
    )
    items = channel_data.get("items") or []
    if not items:
        return {"channel_id": channel_id, "videos": []}

    item = items[0]
    snippet = item.get("snippet") or {}
    statistics = item.get("statistics") or {}
    return {
        "channel_id": channel_id,
        "title": snippet.get("title") or "",
        "description": snippet.get("description") or "",
        "custom_url": snippet.get("customUrl") or "",
        "published_at": snippet.get("publishedAt") or "",
        "url": f"https://www.youtube.com/channel/{channel_id}",
        "thumbnail": thumbnail(snippet),
        "statistics": {
            "subscriber_count": statistics.get("subscriberCount"),
            "video_count": statistics.get("videoCount"),
            "view_count": statistics.get("viewCount"),
        },
        "videos": channel_videos(api_key, channel_id, limit=limit),
    }


def channel_videos(api_key: str, channel: str, *, limit: int = 10) -> list[dict[str, Any]]:
    channel_id = resolve_channel_id(api_key, channel)
    channel_data = youtube_get(
        api_key,
        "channels",
        {"part": "contentDetails,snippet", "id": channel_id, "maxResults": 1},
    )
    items = channel_data.get("items") or []
    if not items:
        return []
    uploads = (
        items[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )
    if not isinstance(uploads, str):
        return []

    response = youtube_get(
        api_key,
        "playlistItems",
        {
            "part": "snippet,contentDetails",
            "playlistId": uploads,
            "maxResults": clamp_limit(limit),
        },
    )
    videos: list[dict[str, Any]] = []
    for item in response.get("items") or []:
        snippet = item.get("snippet") or {}
        content = item.get("contentDetails") or {}
        video_id = content.get("videoId")
        if not isinstance(video_id, str):
            continue
        videos.append(
            {
                "video_id": video_id,
                "title": snippet.get("title") or "",
                "channel_id": snippet.get("channelId") or channel_id,
                "channel_title": snippet.get("channelTitle") or "",
                "published_at": content.get("videoPublishedAt")
                or snippet.get("publishedAt")
                or "",
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": thumbnail(snippet),
            }
        )
    return videos


def search(
    api_key: str,
    query: str,
    *,
    limit: int = 10,
    order: str = "relevance",
    result_type: str = "video",
    channel: str = "",
    published_after: str = "",
    published_before: str = "",
) -> list[dict[str, Any]]:
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": clamp_limit(limit),
        "order": order,
        "type": result_type,
    }
    if channel:
        params["channelId"] = resolve_channel_id(api_key, channel)
    if published_after:
        params["publishedAfter"] = published_after
    if published_before:
        params["publishedBefore"] = published_before

    response = youtube_get(api_key, "search", params)
    results: list[dict[str, Any]] = []
    for item in response.get("items") or []:
        if not isinstance(item, dict):
            continue
        snippet = item.get("snippet") or {}
        identifier = item.get("id") or {}
        kind = identifier.get("kind") or ""
        resource_id = search_resource_id(identifier)
        results.append(
            {
                "kind": kind,
                "id": resource_id,
                "title": snippet.get("title") or "",
                "description": snippet.get("description") or "",
                "channel_id": snippet.get("channelId") or "",
                "channel_title": snippet.get("channelTitle") or "",
                "published_at": snippet.get("publishedAt") or "",
                "url": search_url(kind, resource_id),
                "thumbnail": thumbnail(snippet),
            }
        )
    return results


def resolve_channel_id(api_key: str, channel: str) -> str:
    cached = CHANNEL_CACHE.get(channel)
    if cached:
        return cached

    value = channel.strip()
    if value.startswith("UC"):
        CHANNEL_CACHE[channel] = value
        return value

    path = urlparse(value).path.strip("/")
    parts = path.split("/") if path else [value]
    handle = next((part for part in parts if part.startswith("@")), value)
    response = youtube_get(
        api_key,
        "channels",
        {"part": "id", "forHandle": handle, "maxResults": 1},
    )
    items = response.get("items") or []
    if not items or not isinstance(items[0].get("id"), str):
        raise ValueError(f"could not resolve YouTube channel: {channel}")
    CHANNEL_CACHE[channel] = items[0]["id"]
    return items[0]["id"]


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, 50))


def search_resource_id(identifier: dict[str, Any]) -> str:
    for key in ("videoId", "channelId", "playlistId"):
        value = identifier.get(key)
        if isinstance(value, str):
            return value
    return ""


def search_url(kind: str, resource_id: str) -> str:
    if not resource_id:
        return ""
    if kind == "youtube#video":
        return f"https://www.youtube.com/watch?v={resource_id}"
    if kind == "youtube#channel":
        return f"https://www.youtube.com/channel/{resource_id}"
    if kind == "youtube#playlist":
        return f"https://www.youtube.com/playlist?list={resource_id}"
    return ""


def youtube_get(api_key: str, resource: str, params: dict[str, Any]) -> dict[str, Any]:
    response = httpx.get(
        f"https://www.googleapis.com/youtube/v3/{resource}",
        params={**params, "key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else {}


def thumbnail(snippet: dict[str, Any]) -> str:
    thumbnails = snippet.get("thumbnails") or {}
    for key in ("maxres", "standard", "high", "medium", "default"):
        url = (thumbnails.get(key) or {}).get("url")
        if isinstance(url, str):
            return url
    return ""

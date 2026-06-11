from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
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


def video(url: str) -> dict[str, Any]:
    info = extract(url)
    return {
        "id": info.get("id") or "",
        "title": info.get("title") or "",
        "channel": info.get("channel") or info.get("uploader") or "",
        "channel_id": info.get("channel_id") or "",
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date") or "",
        "description": info.get("description") or "",
        "webpage_url": info.get("webpage_url") or url,
        "thumbnail": info.get("thumbnail") or "",
        "tags": info.get("tags") or [],
        "chapters": info.get("chapters") or [],
        "subtitles": sorted((info.get("subtitles") or {}).keys()),
        "automatic_captions": sorted((info.get("automatic_captions") or {}).keys()),
    }


def transcript(url: str, *, language: str = "en") -> dict[str, Any]:
    info = extract(url)
    tracks = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    source = "subtitles"
    candidates = tracks.get(language)
    if not candidates:
        source = "automatic_captions"
        candidates = automatic.get(language)
    if not candidates:
        return {
            "id": info.get("id") or "",
            "language": language,
            "source": "",
            "segments": [],
            "text": "",
            "available": {
                "subtitles": sorted(tracks.keys()),
                "automatic_captions": sorted(automatic.keys()),
            },
        }

    track = prefer_transcript_track(candidates)
    response = httpx.get(track["url"], timeout=30)
    response.raise_for_status()
    segments = parse_vtt(response.text)
    return {
        "id": info.get("id") or "",
        "title": info.get("title") or "",
        "language": language,
        "source": source,
        "segments": segments,
        "text": " ".join(segment["text"] for segment in segments),
    }


def frames(url: str, *, timestamps: list[str], output_dir: Path) -> list[dict[str, Any]]:
    timestamps = normalize_timestamps(timestamps)
    if not timestamps:
        raise ValueError("at least one timestamp is required")
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required to extract frames")

    output_dir.mkdir(parents=True, exist_ok=True)
    info = extract(url)
    video_url = media_url(info)
    outputs = []
    for index, timestamp in enumerate(timestamps, start=1):
        target = output_dir / f"{info.get('id') or 'youtube'}-{index}.jpg"
        command = [
            "ffmpeg",
            "-y",
            "-ss",
            timestamp,
            "-i",
            video_url,
            "-frames:v",
            "1",
            str(target),
        ]
        run_ffmpeg(command, f"ffmpeg failed at timestamp {timestamp}")
        outputs.append({"timestamp": timestamp, "path": str(target)})
    return outputs


def download(url: str, *, output_dir: Path) -> dict[str, Any]:
    try:
        from yt_dlp import YoutubeDL
    except ImportError as error:
        raise ValueError("yt-dlp is required") from error

    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]",
        "merge_output_format": "mp4",
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        if not isinstance(info, dict):
            raise ValueError("yt-dlp did not return video metadata")
        prepared = Path(ydl.prepare_filename(info))

    path = prepared.with_suffix(".mp4")
    if not path.exists() and prepared.exists():
        path = prepared
    return {
        "id": info.get("id") or "",
        "title": info.get("title") or "",
        "path": str(path),
    }


def clip(
    url: str,
    *,
    start: str,
    duration: float,
    output: Path,
    crop: str = "",
    scale: str = "1280:-2",
    audio: bool = False,
) -> dict[str, Any]:
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required to extract clips")

    output.parent.mkdir(parents=True, exist_ok=True)
    info = extract(url)
    filters = video_filters(crop=crop, scale=scale)
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        start,
        "-t",
        str(duration),
        "-i",
        media_url(info),
        "-vf",
        filters,
    ]
    if not audio:
        command.append("-an")
    command.append(str(output))
    run_ffmpeg(command, f"ffmpeg failed for clip at {start}")
    return {
        "id": info.get("id") or "",
        "title": info.get("title") or "",
        "start": start,
        "duration": duration,
        "crop": crop,
        "scale": scale,
        "path": str(output),
    }


def gif(
    url: str,
    *,
    start: str,
    duration: float,
    output: Path,
    crop: str = "",
    width: int = 640,
    fps: int = 12,
) -> dict[str, Any]:
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required to export gifs")

    output.parent.mkdir(parents=True, exist_ok=True)
    info = extract(url)
    source = media_url(info)
    scale = f"{width}:-1"
    filters = video_filters(crop=crop, scale=scale, fps=fps)
    with tempfile.TemporaryDirectory() as directory:
        palette = Path(directory) / "palette.png"
        run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-ss",
                start,
                "-t",
                str(duration),
                "-i",
                source,
                "-vf",
                f"{filters},palettegen",
                str(palette),
            ],
            f"ffmpeg failed to create gif palette at {start}",
        )
        run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-ss",
                start,
                "-t",
                str(duration),
                "-i",
                source,
                "-i",
                str(palette),
                "-lavfi",
                f"{filters}[x];[x][1:v]paletteuse",
                str(output),
            ],
            f"ffmpeg failed to export gif at {start}",
        )
    return {
        "id": info.get("id") or "",
        "title": info.get("title") or "",
        "start": start,
        "duration": duration,
        "crop": crop,
        "width": width,
        "fps": fps,
        "path": str(output),
    }


def extract(url: str) -> dict[str, Any]:
    try:
        from yt_dlp import YoutubeDL
    except ImportError as error:
        raise ValueError("yt-dlp is required") from error

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if not isinstance(info, dict):
        raise ValueError("yt-dlp did not return video metadata")
    return info


def thumbnail(snippet: dict[str, Any]) -> str:
    thumbnails = snippet.get("thumbnails") or {}
    for key in ("maxres", "standard", "high", "medium", "default"):
        url = (thumbnails.get(key) or {}).get("url")
        if isinstance(url, str):
            return url
    return ""


def prefer_transcript_track(tracks: list[dict[str, Any]]) -> dict[str, Any]:
    for ext in ("vtt", "srv3", "ttml"):
        for track in tracks:
            if track.get("ext") == ext and isinstance(track.get("url"), str):
                return track
    for track in tracks:
        if isinstance(track.get("url"), str):
            return track
    raise ValueError("no usable transcript track")


def parse_vtt(text: str) -> list[dict[str, str]]:
    segments: list[dict[str, str]] = []
    lines = [line.strip() for line in text.splitlines()]
    index = 0
    while index < len(lines):
        line = lines[index]
        if "-->" not in line:
            index += 1
            continue
        start, end = [part.strip().split(" ", 1)[0] for part in line.split("-->", 1)]
        index += 1
        content: list[str] = []
        while index < len(lines) and lines[index]:
            if not lines[index].startswith(("NOTE", "STYLE")):
                content.append(lines[index])
            index += 1
        if content:
            value = clean_caption_text(" ".join(content))
            if value and (not segments or segments[-1]["text"] != value):
                segments.append({"start": start, "end": end, "text": value})
    return dedupe_caption_segments(segments)


def clean_caption_text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", value)).split())


def normalize_timestamps(timestamps: list[str]) -> list[str]:
    values: list[str] = []
    for timestamp in timestamps:
        for part in str(timestamp).split(","):
            value = part.strip()
            if value:
                values.append(value)
    return values


def dedupe_caption_segments(segments: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    for segment in segments:
        text = segment["text"]
        if not deduped:
            deduped.append(segment)
            continue
        previous = deduped[-1]
        previous_text = previous["text"]
        if text in previous_text:
            previous["end"] = segment["end"]
            continue
        if previous_text in text:
            previous["text"] = text
            previous["end"] = segment["end"]
            continue
        overlap = suffix_prefix_overlap(previous_text, text)
        if overlap:
            previous["text"] = previous_text + text[overlap:]
            previous["end"] = segment["end"]
            continue
        deduped.append(segment)
    return deduped


def suffix_prefix_overlap(left: str, right: str) -> int:
    for size in range(min(len(left), len(right)), 7, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def media_url(info: dict[str, Any]) -> str:
    formats = info.get("formats")
    if not isinstance(formats, list):
        raise ValueError("yt-dlp returned no media formats")
    for item in reversed(formats):
        if isinstance(item, dict) and item.get("vcodec") != "none" and isinstance(item.get("url"), str):
            return item["url"]
    raise ValueError("yt-dlp returned no video format URL")


def video_filters(*, crop: str = "", scale: str = "", fps: int | None = None) -> str:
    filters = []
    if crop:
        filters.append(f"crop={crop}")
    if fps is not None:
        filters.append(f"fps={fps}")
    if scale:
        filters.append(f"scale={scale}")
    return ",".join(filters) if filters else "null"


def run_ffmpeg(command: list[str], message: str) -> None:
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        lines = (error.stderr or "").strip().splitlines()
        detail = lines[-1] if lines else "unknown ffmpeg error"
        raise ValueError(f"{message}: {detail}") from error

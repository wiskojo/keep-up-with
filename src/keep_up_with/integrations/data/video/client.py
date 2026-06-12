from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import httpx

from keep_up_with.integrations.data.common import resolve_path


def info(source: str) -> dict[str, Any]:
    local = local_path(source)
    if local is not None:
        return probe(local)
    data = extract(source)
    return {
        "id": data.get("id") or "",
        "title": data.get("title") or "",
        "channel": data.get("channel") or data.get("uploader") or "",
        "channel_id": data.get("channel_id") or "",
        "duration": data.get("duration"),
        "upload_date": data.get("upload_date") or "",
        "description": data.get("description") or "",
        "webpage_url": data.get("webpage_url") or source,
        "thumbnail": data.get("thumbnail") or "",
        "tags": data.get("tags") or [],
        "chapters": data.get("chapters") or [],
        "subtitles": sorted((data.get("subtitles") or {}).keys()),
        "automatic_captions": sorted((data.get("automatic_captions") or {}).keys()),
    }


def transcript(source: str, *, language: str = "en") -> dict[str, Any]:
    if local_path(source) is not None:
        raise ValueError("transcripts need a video URL with caption tracks, not a local file")
    info = extract(source)
    tracks = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    source_kind, matched, candidates = transcript_candidates(tracks, automatic, language)
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
        "language": matched,
        "source": source_kind,
        "segments": segments,
        "text": " ".join(segment["text"] for segment in segments),
    }


def frames(source: str, *, timestamps: list[str], output_dir: Path) -> list[dict[str, Any]]:
    timestamps = normalize_timestamps(timestamps)
    if not timestamps:
        raise ValueError("at least one timestamp is required")
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required to extract frames")

    output_dir.mkdir(parents=True, exist_ok=True)
    input_url, stem = ffmpeg_input(source)
    outputs = []
    for index, timestamp in enumerate(timestamps, start=1):
        target = output_dir / f"{stem}-{index}.jpg"
        command = [
            "ffmpeg",
            "-y",
            "-ss",
            timestamp,
            "-i",
            input_url,
            "-frames:v",
            "1",
            str(target),
        ]
        run_ffmpeg(command, f"ffmpeg failed at timestamp {timestamp}")
        outputs.append({"timestamp": timestamp, "path": str(target)})
    return outputs


def clip(
    source: str,
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
    input_url, _ = ffmpeg_input(source)
    filters = video_filters(crop=crop, scale=scale)
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        start,
        "-t",
        str(duration),
        "-i",
        input_url,
        "-vf",
        filters,
    ]
    if not audio:
        command.append("-an")
    command.append(str(output))
    run_ffmpeg(command, f"ffmpeg failed for clip at {start}")
    return {
        "source": source,
        "start": start,
        "duration": duration,
        "crop": crop,
        "scale": scale,
        "path": str(output),
    }


def gif(
    source: str,
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
    input_url, _ = ffmpeg_input(source)
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
                input_url,
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
                input_url,
                "-i",
                str(palette),
                "-lavfi",
                f"{filters}[x];[x][1:v]paletteuse",
                str(output),
            ],
            f"ffmpeg failed to export gif at {start}",
        )
    return {
        "source": source,
        "start": start,
        "duration": duration,
        "crop": crop,
        "width": width,
        "fps": fps,
        "path": str(output),
    }


def local_path(source: str) -> Path | None:
    if source.startswith(("http://", "https://")):
        return None
    path = resolve_path(source)
    if path.exists():
        return path
    raise ValueError(f"source is not a URL or an existing file: {source}")


def ffmpeg_input(source: str) -> tuple[str, str]:
    """Return the ffmpeg input and an output filename stem for the source."""
    local = local_path(source)
    if local is not None:
        return str(local), local.stem
    data = extract(source)
    return media_url(data), str(data.get("id") or "video")


def probe(path: Path) -> dict[str, Any]:
    if shutil.which("ffprobe") is None:
        raise ValueError("ffprobe is required to inspect local videos")
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        lines = (error.stderr or "").strip().splitlines()
        detail = lines[-1] if lines else "unknown ffprobe error"
        raise ValueError(f"ffprobe failed for {path}: {detail}") from error

    data = json.loads(result.stdout or "{}")
    fmt = data.get("format") or {}
    stream = next(
        (item for item in data.get("streams") or [] if item.get("codec_type") == "video"),
        {},
    )
    return {
        "path": str(path),
        "duration": float(fmt["duration"]) if fmt.get("duration") else None,
        "format": fmt.get("format_name") or "",
        "size": int(fmt["size"]) if fmt.get("size") else None,
        "width": stream.get("width"),
        "height": stream.get("height"),
        "codec": stream.get("codec_name") or "",
        "frame_rate": parse_frame_rate(str(stream.get("avg_frame_rate") or "")),
    }


def parse_frame_rate(value: str) -> float | None:
    numerator, _, denominator = value.partition("/")
    try:
        if denominator:
            return round(float(numerator) / float(denominator), 3) if float(denominator) else None
        return float(numerator) if numerator else None
    except ValueError:
        return None


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


def media_url(info: dict[str, Any]) -> str:
    formats = info.get("formats")
    if not isinstance(formats, list):
        raise ValueError("yt-dlp returned no media formats")
    for item in reversed(formats):
        if isinstance(item, dict) and item.get("vcodec") != "none" and isinstance(item.get("url"), str):
            return item["url"]
    raise ValueError("yt-dlp returned no video format URL")


def transcript_candidates(
    tracks: dict[str, Any],
    automatic: dict[str, Any],
    language: str,
) -> tuple[str, str, list[dict[str, Any]]]:
    for source, available in (("subtitles", tracks), ("automatic_captions", automatic)):
        for key in transcript_language_keys(available, language):
            candidates = available.get(key)
            if candidates:
                return source, key, candidates
    return "", language, []


def transcript_language_keys(available: dict[str, Any], language: str) -> list[str]:
    prefixes = [language, "en"] if language != "en" else [language]
    keys: list[str] = []
    for prefix in prefixes:
        keys.append(prefix)
        keys.extend(
            key for key in sorted(available) if key.startswith((f"{prefix}-", f"{prefix}_"))
        )
    # The "-orig" track is the video's original spoken language.
    keys.extend(key for key in sorted(available) if key.endswith("-orig") and key not in keys)
    return keys


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

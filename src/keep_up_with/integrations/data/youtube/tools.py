from __future__ import annotations

from pathlib import Path
from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.youtube import client


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@tool("Fetch YouTube video metadata.")
def video(_ctx: ToolContext, url: str) -> dict[str, Any]:
    return client.video(url)


@tool("Fetch a YouTube transcript.")
def transcript(_ctx: ToolContext, url: str, language: str = "en") -> dict[str, Any]:
    return client.transcript(url, language=language)


@tool("Extract frames from a YouTube video.")
def frames(
    _ctx: ToolContext,
    url: str,
    timestamps: list[str],
    output_dir: str = ".",
) -> list[dict[str, Any]]:
    return client.frames(url, timestamps=timestamps, output_dir=resolve_path(output_dir))


@tool("Download a local YouTube source copy for clips.")
def download(
    _ctx: ToolContext,
    url: str,
    output_dir: str = ".",
) -> dict[str, Any]:
    return client.download(url, output_dir=resolve_path(output_dir))


@tool("Extract a short muted YouTube clip.")
def clip(
    _ctx: ToolContext,
    url: str,
    start: str,
    duration: float,
    output: str,
    crop: str = "",
    scale: str = "1280:-2",
    audio: bool = False,
) -> dict[str, Any]:
    return client.clip(
        url,
        start=start,
        duration=duration,
        output=resolve_path(output),
        crop=crop,
        scale=scale,
        audio=audio,
    )


@tool("Export a short YouTube clip as a GIF.")
def gif(
    _ctx: ToolContext,
    url: str,
    start: str,
    duration: float,
    output: str,
    crop: str = "",
    width: int = 640,
    fps: int = 12,
) -> dict[str, Any]:
    return client.gif(
        url,
        start=start,
        duration=duration,
        output=resolve_path(output),
        crop=crop,
        width=width,
        fps=fps,
    )

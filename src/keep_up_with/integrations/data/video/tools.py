from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import resolve_path
from keep_up_with.integrations.data.video import client


@tool("Show metadata for a video URL or local file")
def info(ctx: ToolContext, source: str) -> dict[str, Any]:
    del ctx
    return client.info(source)


@tool("Show a transcript for a video URL")
def transcript(ctx: ToolContext, source: str, language: str = "en") -> dict[str, Any]:
    del ctx
    return client.transcript(source, language=language)


@tool("Extract frames from a video URL or local file")
def frames(
    ctx: ToolContext,
    source: str,
    timestamps: list[str],
    output_dir: str = ".",
) -> list[dict[str, Any]]:
    del ctx
    return client.frames(source, timestamps=timestamps, output_dir=resolve_path(output_dir))


@tool("Export a clip from a video URL or local file")
def clip(
    ctx: ToolContext,
    source: str,
    start: str,
    duration: float,
    output: str,
    crop: str = "",
    scale: str = "1280:-2",
    audio: bool = False,
) -> dict[str, Any]:
    del ctx
    return client.clip(
        source,
        start=start,
        duration=duration,
        output=resolve_path(output),
        crop=crop,
        scale=scale,
        audio=audio,
    )


@tool("Export a GIF from a video URL or local file")
def gif(
    ctx: ToolContext,
    source: str,
    start: str,
    duration: float,
    output: str,
    crop: str = "",
    width: int = 640,
    fps: int = 12,
) -> dict[str, Any]:
    del ctx
    return client.gif(
        source,
        start=start,
        duration=duration,
        output=resolve_path(output),
        crop=crop,
        width=width,
        fps=fps,
    )

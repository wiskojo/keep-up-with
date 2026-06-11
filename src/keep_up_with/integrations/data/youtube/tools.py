from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import resolve_path
from keep_up_with.integrations.data.youtube import client


@tool("Fetch YouTube video metadata.")
def video(ctx: ToolContext, url: str) -> dict[str, Any]:
    del ctx
    return client.video(url)


@tool("Search YouTube.")
def search(
    ctx: ToolContext,
    query: str,
    limit: int = 10,
    order: str = "relevance",
    result_type: str = "video",
    channel: str = "",
    published_after: str = "",
    published_before: str = "",
) -> list[dict[str, Any]]:
    return client.search(
        ctx.env("YOUTUBE_API_KEY"),
        query,
        limit=limit,
        order=order,
        result_type=result_type,
        channel=channel,
        published_after=published_after,
        published_before=published_before,
    )


@tool("Fetch YouTube channel metadata and recent videos.")
def channel(ctx: ToolContext, channel: str, limit: int = 10) -> dict[str, Any]:
    return client.channel(
        ctx.env("YOUTUBE_API_KEY"),
        channel,
        limit=limit,
    )


@tool("Fetch a YouTube transcript.")
def transcript(ctx: ToolContext, url: str, language: str = "en") -> dict[str, Any]:
    del ctx
    return client.transcript(url, language=language)


@tool("Extract frames from a YouTube video.")
def frames(
    ctx: ToolContext,
    url: str,
    timestamps: list[str],
    output_dir: str = ".",
) -> list[dict[str, Any]]:
    del ctx
    return client.frames(url, timestamps=timestamps, output_dir=resolve_path(output_dir))


@tool("Download a local YouTube source copy for clips.")
def download(
    ctx: ToolContext,
    url: str,
    output_dir: str = ".",
) -> dict[str, Any]:
    del ctx
    return client.download(url, output_dir=resolve_path(output_dir))


@tool("Extract a short muted YouTube clip.")
def clip(
    ctx: ToolContext,
    url: str,
    start: str,
    duration: float,
    output: str,
    crop: str = "",
    scale: str = "1280:-2",
    audio: bool = False,
) -> dict[str, Any]:
    del ctx
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
    ctx: ToolContext,
    url: str,
    start: str,
    duration: float,
    output: str,
    crop: str = "",
    width: int = 640,
    fps: int = 12,
) -> dict[str, Any]:
    del ctx
    return client.gif(
        url,
        start=start,
        duration=duration,
        output=resolve_path(output),
        crop=crop,
        width=width,
        fps=fps,
    )

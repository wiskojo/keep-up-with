from __future__ import annotations

from pathlib import Path
from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.youtube import client


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
    target = Path(output_dir).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    return client.frames(url, timestamps=timestamps, output_dir=target)

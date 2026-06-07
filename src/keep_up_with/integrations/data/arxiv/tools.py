from __future__ import annotations

from pathlib import Path
from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.arxiv import client


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@tool("Download an arXiv PDF, best-effort Markdown, raw source, and figure inventory.")
def download(
    _ctx: ToolContext,
    id_or_url: str,
    output_dir: str = "research/artifacts/arxiv",
) -> dict[str, Any]:
    return client.download(
        id_or_url,
        output_dir=resolve_path(output_dir),
    )

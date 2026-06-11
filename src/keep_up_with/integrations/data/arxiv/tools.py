from __future__ import annotations

from typing import Any

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.arxiv import client
from keep_up_with.integrations.data.common import resolve_path


@tool("Download an arXiv paper and artifacts")
def download(
    _ctx: ToolContext,
    id_or_url: str,
    output_dir: str = "research/artifacts/arxiv",
) -> dict[str, Any]:
    return client.download(
        id_or_url,
        output_dir=resolve_path(output_dir),
    )

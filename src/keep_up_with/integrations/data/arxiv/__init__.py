from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.arxiv.tools import download


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="arxiv",
            description="Fetch arXiv PDFs, Markdown, source bundles, and figures.",
            tools=(download,),
            tools_require_enabled=False,
        )
    )

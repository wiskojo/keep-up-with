from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.arxiv.tools import download


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="arxiv",
            description="Fetch arXiv papers and artifacts",
            tools=(download,),
        )
    )

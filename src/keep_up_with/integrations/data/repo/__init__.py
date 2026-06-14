from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.repo.tools import star_history


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="repo",
            description="Repository metadata and comparisons",
            tools=(star_history,),
        )
    )

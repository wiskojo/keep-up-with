from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.video import tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="video",
            description="Video sources and files",
            tools=(
                tools.info,
                tools.transcript,
                tools.frames,
                tools.clip,
                tools.gif,
            ),
        )
    )

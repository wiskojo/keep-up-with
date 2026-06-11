from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.image import tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="image",
            description="Crop and inspect image assets",
            tools=(tools.crop, tools.grid),
        )
    )

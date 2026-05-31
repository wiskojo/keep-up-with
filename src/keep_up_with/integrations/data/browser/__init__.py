from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.browser.tools import history


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="browser",
            description="Search local browser history.",
            tools=(history,),
        )
    )

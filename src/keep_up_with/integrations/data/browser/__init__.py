from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.browser.tools import history


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="browser",
            description="Search browser history",
            tools=(history,),
        )
    )

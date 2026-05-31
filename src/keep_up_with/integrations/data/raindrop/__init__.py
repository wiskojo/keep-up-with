from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.raindrop.subscription import bookmarks as bookmark_subscription
from keep_up_with.integrations.data.raindrop.tools import bookmarks


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="raindrop",
            description="Search saved bookmarks.",
            subscriptions=(bookmark_subscription,),
            tools=(bookmarks,),
            required_env=("RAINDROP_TOKEN",),
            default_settings={
                "since": "PT10M",
                "limit": 200,
            },
        )
    )

from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration
from keep_up_with.integrations.data.raindrop import subscription, tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="raindrop",
            description="Saved bookmarks",
            subscriptions=(subscription.bookmarks,),
            tools=(tools.bookmarks,),
            required_env=("RAINDROP_TOKEN",),
            default_settings={
                "since": "PT10M",
                "limit": 200,
            },
            setup_default_enabled=False,
        )
    )

from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.youtube import subscription, tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="youtube",
            description="YouTube videos and channels",
            subscriptions=(subscription.videos,),
            tools=(
                tools.search,
                tools.channel,
            ),
            required_env=("YOUTUBE_API_KEY",),
            parameters=(
                IntegrationParameter(
                    name="channels",
                    help="@AndrejKarpathy, channel IDs, or channel URLs",
                ),
            ),
        )
    )

from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.youtube import subscription, tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="youtube",
            description="Search YouTube and extract video assets",
            subscriptions=(subscription.videos,),
            tools=(
                tools.search,
                tools.channel,
                tools.video,
                tools.transcript,
                tools.frames,
                tools.download,
                tools.clip,
                tools.gif,
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

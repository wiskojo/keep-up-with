from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.youtube.subscription import videos as videos_subscription
from keep_up_with.integrations.data.youtube.tools import (
    channel,
    clip,
    download,
    frames,
    gif,
    search,
    transcript,
    video,
)


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="youtube",
            description="Search YouTube and fetch videos, transcripts, frames, and clips.",
            subscriptions=(videos_subscription,),
            tools=(search, channel, video, transcript, frames, download, clip, gif),
            required_env=("YOUTUBE_API_KEY",),
            parameters=(
                IntegrationParameter(
                    name="channels",
                    help="@AndrejKarpathy, channel IDs, or channel URLs",
                ),
            ),
        )
    )

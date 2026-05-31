from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.youtube.subscription import videos
from keep_up_with.integrations.data.youtube.tools import frames, transcript, video


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="youtube",
            description="Fetch videos, transcripts, and frames.",
            subscriptions=(videos,),
            tools=(video, transcript, frames),
            required_env=("YOUTUBE_API_KEY",),
            parameters=(
                IntegrationParameter(
                    name="channels",
                    help="@AndrejKarpathy, channel IDs, or channel URLs",
                ),
            ),
        )
    )

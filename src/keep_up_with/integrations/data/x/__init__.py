from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.x.subscription import posts
from keep_up_with.integrations.data.x.tools import download, search, timeline, user


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="x",
            description="X posts, accounts, and timelines",
            subscriptions=(posts,),
            tools=(search, download, user, timeline),
            required_env=("X_BEARER_TOKEN",),
            parameters=(
                IntegrationParameter(
                    name="accounts",
                    help="karpathy, omarsar0",
                ),
            ),
        )
    )

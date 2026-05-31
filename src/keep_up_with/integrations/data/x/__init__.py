from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.x.subscription import posts
from keep_up_with.integrations.data.x.tools import post, search, timeline, user


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="x",
            description="Search X posts and accounts.",
            subscriptions=(posts,),
            tools=(search, post, user, timeline),
            required_env=("X_BEARER_TOKEN",),
            parameters=(
                IntegrationParameter(
                    name="accounts",
                    help="karpathy, omarsar0",
                ),
            ),
            default_settings={
                "limit": 10,
            },
        )
    )

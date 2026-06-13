from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.reddit import subscription, tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="reddit",
            description="Reddit posts and threads",
            subscriptions=(subscription.posts,),
            tools=(tools.posts, tools.search, tools.thread),
            required_env=(
                "REDDIT_CLIENT_ID",
                "REDDIT_CLIENT_SECRET",
            ),
            parameters=(
                IntegrationParameter(
                    name="subreddits",
                    help="LocalLLaMA, codex, ClaudeAI",
                ),
            ),
            default_settings={
                "limit": 25,
                "window_hours": 24,
            },
        )
    )

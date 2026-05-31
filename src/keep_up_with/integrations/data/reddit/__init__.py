from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.reddit.subscription import posts
from keep_up_with.integrations.data.reddit.tools import posts as posts_tool
from keep_up_with.integrations.data.reddit.tools import search, thread


def register(registry) -> None:
    registry.data(
        DataIntegration(
            name="reddit",
            description="Search Reddit posts and threads.",
            subscriptions=(posts,),
            tools=(posts_tool, search, thread),
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

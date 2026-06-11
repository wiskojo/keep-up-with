from __future__ import annotations

from keep_up_with.integrations.base import MessagingIntegration
from keep_up_with.integrations.messaging.discord.client import DiscordMessagingClient
from keep_up_with.integrations.messaging.discord.setup import BOT_TOKEN_ENV
from keep_up_with.integrations.messaging.discord.setup import configure as configure_setup
from keep_up_with.integrations.messaging.discord.subscription import messages


def register(registry) -> None:
    registry.add_messaging(
        MessagingIntegration(
            name="discord",
            client=DiscordMessagingClient,
            subscriptions=(messages,),
            required_env=(BOT_TOKEN_ENV,),
            required_settings=("server_id", "user_id"),
            setup=configure_setup,
        )
    )

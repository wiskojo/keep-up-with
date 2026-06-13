from __future__ import annotations

from keep_up_with.integrations.base import MessagingIntegration
from keep_up_with.integrations.messaging.file.client import FileMessagingClient


def register(registry) -> None:
    registry.add_messaging(
        MessagingIntegration(
            name="file",
            client=FileMessagingClient,
        )
    )

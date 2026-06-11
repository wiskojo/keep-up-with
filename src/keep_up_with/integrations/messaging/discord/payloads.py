from __future__ import annotations

from typing import Any

import discord


def message_data(message: discord.Message) -> dict[str, Any]:
    return {
        "message_id": str(message.id),
        "channel_id": str(message.channel.id),
        "author_id": str(message.author.id),
        "author_name": str(message.author),
        "content": message.content,
        "url": message.jump_url,
        "attachments": [attachment_data(item) for item in message.attachments],
        "created_at": message.created_at.isoformat(),
    }


def attachment_data(attachment: discord.Attachment) -> dict[str, Any]:
    return {
        "id": str(attachment.id),
        "filename": attachment.filename,
        "url": attachment.url,
        "proxy_url": attachment.proxy_url,
        "content_type": attachment.content_type,
        "size": attachment.size,
        "description": attachment.description,
        "width": attachment.width,
        "height": attachment.height,
    }

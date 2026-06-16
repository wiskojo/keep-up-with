from __future__ import annotations

import discord

from keep_up_with.integrations.base import SubscriptionContext, subscription
from keep_up_with.integrations.messaging.discord.payloads import message_data


@subscription("discord.messages")
def messages(ctx: SubscriptionContext) -> None:
    token = ctx.env("DISCORD_BOT_TOKEN")
    admin_ids = _admin_user_ids(ctx.settings())

    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_message(message) -> None:
        if message.author.bot:
            return
        data = message_data(message)
        role = _actor_role(str(message.author.id), admin_ids)
        data["actor_role"] = role
        data["actor"] = {
            "id": data["author_id"],
            "name": data["author_name"],
            "role": role,
        }
        data["reply_to"] = await _reply_context(message)
        text = " ".join(str(data.get("content") or "").split())
        if not text and data.get("attachments"):
            text = f"{len(data['attachments'])} attachment(s)"
        ctx.emit(
            kind="message",
            external_id=data["message_id"],
            summary=(
                f"{data.get('author_name') or data.get('author_id')} ({role}): {text}"
            ),
            summary_limit=1200,
            high_priority=True,
            refs={
                "channel_id": data.get("channel_id", ""),
                "message_id": data.get("message_id", ""),
            },
            data=data,
        )

    @client.event
    async def on_raw_reaction_add(payload) -> None:
        if str(payload.user_id) not in admin_ids:
            return
        data = _reaction_data(payload)
        data["actor_role"] = "admin"
        message = await _reaction_message(client, payload)
        if message is not None:
            data["target_message"] = message_data(message)
        emoji = data.get("emoji") or data.get("emoji_name") or "reaction"
        ctx.emit(
            kind="reaction_add",
            external_id=f"{data['message_id']}:{data['user_id']}:{emoji}",
            summary=f"{data.get('user_name') or data.get('user_id')}: reacted with {emoji}",
            refs={
                "channel_id": data.get("channel_id", ""),
                "message_id": data.get("message_id", ""),
            },
            data=data,
        )

    client.run(token)


def _admin_user_ids(settings: dict) -> set[str]:
    user_id = str(settings["user_id"])
    values = settings.get("admin_user_ids") or []
    if isinstance(values, str):
        values = [values]
    return {user_id, *(str(value) for value in values if str(value))}


def _actor_role(user_id: str, admin_ids: set[str]) -> str:
    return "admin" if user_id in admin_ids else "member"


async def _reply_context(message) -> dict | None:
    reference = message.reference
    if reference is None or reference.message_id is None:
        return None
    context = {
        "message_id": str(reference.message_id),
        "channel_id": str(reference.channel_id or message.channel.id),
    }
    if isinstance(reference.resolved, discord.Message):
        context.update(message_data(reference.resolved))
        return context
    fetch = getattr(message.channel, "fetch_message", None)
    if not callable(fetch):
        return context
    try:
        referenced = await fetch(int(reference.message_id))
    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
        return context
    context.update(message_data(referenced))
    return context


async def _reaction_message(client, payload):
    try:
        channel = await client.fetch_channel(payload.channel_id)
    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
        return None
    fetch = getattr(channel, "fetch_message", None)
    if not callable(fetch):
        return None
    try:
        return await fetch(payload.message_id)
    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
        return None


def _reaction_data(payload) -> dict:
    data = {
        "message_id": str(payload.message_id),
        "channel_id": str(payload.channel_id),
        "user_id": str(payload.user_id),
        "emoji": str(payload.emoji),
        "emoji_name": payload.emoji.name,
        "emoji_animated": payload.emoji.animated,
    }
    if payload.guild_id is not None:
        data["guild_id"] = str(payload.guild_id)
    if payload.emoji.id is not None:
        data["emoji_id"] = str(payload.emoji.id)
    if payload.member is not None:
        data["user_name"] = str(payload.member)
    return data

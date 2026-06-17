from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import discord

from keep_up_with.integrations.base import (
    ChannelRef,
    MessageRef,
    MessagingContext,
    SectionRef,
    SpaceDeleteItem,
    SpacePlan,
    SpaceResetPreview,
    ThreadPost,
    ThreadRef,
)
from keep_up_with.integrations.messaging.discord.payloads import message_data

DISCORD_MESSAGE_LIMIT = 2000


class DiscordMessagingClient:
    def __init__(self, context: MessagingContext) -> None:
        self.context = context

    @asynccontextmanager
    async def _client(
        self,
        intents: discord.Intents | None = None,
    ) -> AsyncIterator[discord.Client]:
        client = discord.Client(intents=intents or discord.Intents.none())
        try:
            await client.login(self.context.env("DISCORD_BOT_TOKEN"))
            yield client
        finally:
            await client.close()

    async def list_channels(self) -> list[ChannelRef]:
        async with self._client() as client:
            guild = await self._guild(client)
            channels = await guild.fetch_channels()
            sections_by_id = _sections_by_id(channels)
            return [
                _channel_ref(channel, sections_by_id)
                for channel in channels
                if isinstance(channel, discord.TextChannel)
            ]

    async def list_sections(self) -> list[SectionRef]:
        async with self._client() as client:
            guild = await self._guild(client)
            channels = await guild.fetch_channels()
            return [
                _section_ref(channel)
                for channel in channels
                if isinstance(channel, discord.CategoryChannel)
            ]

    async def create_channel(
        self,
        *,
        name: str,
        section: str | None = None,
        description: str | None = None,
    ) -> ChannelRef:
        if not name.strip():
            raise ValueError("name is required")
        async with self._client() as client:
            guild = await self._guild(client)
            category = await self._section(guild, section, create=True) if section else None
            channel = await guild.create_text_channel(
                name=name[:100],
                category=category,
                topic=description[:1024] if description else None,
                reason="keep-up-with space management",
            )
            return _channel_ref(channel, category=category)

    async def apply_space(self, plan: SpacePlan, *, reset: bool = False) -> None:
        async with self._client() as client:
            guild = await self._guild(client)
            channels = await guild.fetch_channels()
            if reset:
                await _delete_channels(channels)
                channels = []

            sections_by_key: dict[str, discord.CategoryChannel] = {}
            sections = [
                channel
                for channel in channels
                if isinstance(channel, discord.CategoryChannel)
            ]
            text_channels = [
                channel
                for channel in channels
                if isinstance(channel, discord.TextChannel)
            ]

            for section in plan.sections:
                category = _find_section(sections, section.name)
                if category is None:
                    category = await guild.create_category(
                        name=section.name[:100],
                        reason="keep-up-with space management",
                    )
                    sections.append(category)
                sections_by_key[section.key] = category

            for channel in plan.channels:
                category = sections_by_key.get(channel.section)
                if category is None:
                    category = _find_section(sections, channel.section)
                if category is None and channel.section:
                    category = await guild.create_category(
                        name=channel.section[:100],
                        reason="keep-up-with space management",
                    )
                    sections.append(category)
                existing = _find_text_channel(text_channels, channel.name, category=category)
                if existing is None:
                    existing = _find_text_channel(text_channels, channel.name)
                if existing is None:
                    created = await self._create_text_channel(
                        guild,
                        name=channel.name,
                        category=category,
                        description=channel.description,
                    )
                    text_channels.append(created)
                    continue

                changes: dict[str, Any] = {"reason": "keep-up-with space management"}
                if category is not None and existing.category_id != category.id:
                    changes["category"] = category
                if channel.description and not (existing.topic or ""):
                    changes["topic"] = channel.description[:1024]
                if len(changes) > 1:
                    updated = await existing.edit(**changes)
                    if updated is not None:
                        text_channels = [
                            updated if item.id == updated.id else item
                            for item in text_channels
                        ]

    async def preview_space_reset(self) -> SpaceResetPreview:
        async with self._client() as client:
            guild = await self._guild(client)
            channels = await guild.fetch_channels()
            return SpaceResetPreview(
                items=_space_delete_items(channels),
                default_empty_server=await _default_empty_server(channels),
                target=f"Discord server: {guild.name} ({guild.id})",
            )

    async def rename_channel(self, *, channel: str, name: str) -> ChannelRef:
        if not name.strip():
            raise ValueError("name is required")
        async with self._client() as client:
            target = await self._text_channel(client, channel)
            sections_by_id = _sections_by_id(await target.guild.fetch_channels())
            updated = await target.edit(
                name=name[:100],
                reason="keep-up-with space management",
            )
            return _channel_ref(updated or target, sections_by_id)

    async def move_channel(
        self,
        *,
        channel: str,
        section: str | None = None,
        before: str | None = None,
        after: str | None = None,
    ) -> ChannelRef:
        if before and after:
            raise ValueError("use before or after, not both")
        if not section and not before and not after:
            raise ValueError("section, before, or after is required")
        async with self._client() as client:
            guild = await self._guild(client)
            target = await self._text_channel(client, channel)
            category = await self._section(guild, section, create=True) if section else None
            sections_by_id = _sections_by_id(await guild.fetch_channels())
            position = None
            if before or after:
                anchor = await self._text_channel(client, before or after or "")
                position = anchor.position + (1 if after else 0)
                if section is None:
                    category = (
                        sections_by_id.get(anchor.category_id)
                        if anchor.category_id
                        else anchor.category
                    )
            changes: dict[str, Any] = {"reason": "keep-up-with space management"}
            if category is not None:
                changes["category"] = category
            if position is not None:
                changes["position"] = position
            updated = await target.edit(**changes)
            return _channel_ref(updated or target, sections_by_id, category=category)

    async def create_section(self, *, name: str) -> SectionRef:
        if not name.strip():
            raise ValueError("name is required")
        async with self._client() as client:
            guild = await self._guild(client)
            section = await guild.create_category(
                name=name[:100],
                reason="keep-up-with space management",
            )
            return _section_ref(section)

    async def rename_section(self, *, section: str, name: str) -> SectionRef:
        if not name.strip():
            raise ValueError("name is required")
        async with self._client() as client:
            category = await self._section(await self._guild(client), section)
            updated = await category.edit(
                name=name[:100],
                reason="keep-up-with space management",
            )
            return _section_ref(updated or category)

    async def move_section(
        self,
        *,
        section: str,
        before: str | None = None,
        after: str | None = None,
    ) -> SectionRef:
        if before and after:
            raise ValueError("use before or after, not both")
        if not before and not after:
            raise ValueError("before or after is required")
        async with self._client() as client:
            guild = await self._guild(client)
            target = await self._section(guild, section)
            anchor = await self._section(guild, before or after or "")
            position = anchor.position + (1 if after else 0)
            updated = await target.edit(
                position=position,
                reason="keep-up-with space management",
            )
            return _section_ref(updated or target)

    async def list_messages(
        self,
        *,
        channel: str | None = None,
        thread_id: str | None = None,
        limit: int = 25,
        query: str | None = None,
        author: str | None = None,
    ) -> list[dict[str, Any]]:
        async with self._client(_message_intents()) as client:
            if channel or thread_id or not query:
                target = await self._message_target(
                    client, channel=channel, thread_id=thread_id
                )
                return await _collect_messages(
                    target, limit=limit, query=query, author=author
                )
            # A query without a channel searches everywhere the bot can read.
            guild = await self._guild(client)
            targets: list[discord.abc.Messageable] = [
                item
                for item in await guild.fetch_channels()
                if isinstance(item, discord.TextChannel)
            ]
            user = await client.fetch_user(int(self.context.settings()["user_id"]))
            targets.append(user.dm_channel or await user.create_dm())
            semaphore = asyncio.Semaphore(8)

            async def collect(target: discord.abc.Messageable) -> list[dict[str, Any]]:
                async with semaphore:
                    try:
                        return await _collect_messages(
                            target, limit=limit, query=query, author=author
                        )
                    except discord.HTTPException:
                        return []

            results = await asyncio.gather(*(collect(target) for target in targets))
            rows = [row for result in results for row in result]
            rows.sort(key=lambda row: row["created_at"])
            return rows

    async def messages_around(
        self,
        *,
        message_id: str,
        channel: str | None = None,
        thread_id: str | None = None,
        before: int = 10,
        after: int = 20,
    ) -> list[dict[str, Any]]:
        async with self._client(_message_intents()) as client:
            target = await self._message_target(
                client, channel=channel, thread_id=thread_id
            )
            anchor = await _fetch_message(target, message_id)
            return await _collect_messages_around(
                target,
                anchor,
                before=max(0, min(before, 100)),
                after=max(0, min(after, 100)),
            )

    async def send_message(
        self,
        *,
        text: str,
        channel: str | None = None,
        thread_id: str | None = None,
        reply_to: str | None = None,
        attachments: list[str] | None = None,
    ) -> MessageRef:
        if not text and not attachments:
            raise ValueError("text or attachment is required")
        _validate_message_text(text)
        files = [_file(path) for path in attachments or []]
        try:
            async with self._client() as client:
                target = await self._message_target(
                    client,
                    channel=channel,
                    thread_id=thread_id,
                )
                reference = await _fetch_message(target, reply_to) if reply_to else None
                try:
                    message = await target.send(
                        content=text or None,
                        files=files or None,
                        reference=reference,
                        mention_author=False,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except discord.HTTPException as error:
                    raise ValueError(_discord_error(error)) from error
                return _message_ref(message)
        finally:
            for file in files:
                file.close()

    async def edit_message(
        self,
        *,
        message_id: str,
        text: str,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> MessageRef:
        if not text:
            raise ValueError("text is required")
        _validate_message_text(text)
        async with self._client() as client:
            target = await self._message_target(client, channel=channel, thread_id=thread_id)
            message = await _own_message(client, target, message_id)
            try:
                updated = await message.edit(content=text)
            except discord.HTTPException as error:
                raise ValueError(_discord_error(error)) from error
            return _message_ref(updated)

    async def delete_message(
        self,
        *,
        message_id: str,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        async with self._client() as client:
            target = await self._message_target(client, channel=channel, thread_id=thread_id)
            message = await _own_message(client, target, message_id)
            await message.delete()

    async def create_thread(
        self,
        *,
        channel: str,
        title: str,
        posts: Sequence[ThreadPost],
        from_message: str | None = None,
    ) -> ThreadRef:
        if not title.strip():
            raise ValueError("title is required")
        if not posts:
            raise ValueError("at least one post is required")
        for index, post in enumerate(posts, start=1):
            if not post.text and not post.attachments:
                raise ValueError(f"post {index} needs text or an attachment")
            _validate_message_text(post.text)
            for path in post.attachments:
                if not Path(path).expanduser().exists():
                    raise ValueError(f"attachment not found: {path}")
        async with self._client(_thread_member_intents()) as client:
            parent = await self._text_channel(client, channel)
            try:
                if from_message:
                    starter = await _fetch_message(parent, from_message)
                    existing = getattr(starter, "thread", None)
                    if existing is not None:
                        raise ValueError(
                            f"message already has a thread: {existing.id}; use thread append"
                    )
                    thread_posts = list(posts)
                else:
                    first_post = posts[0]
                    files = [_file(path) for path in first_post.attachments]
                    try:
                        starter = await parent.send(
                            content=first_post.text or None,
                            files=files or None,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    finally:
                        for file in files:
                            file.close()
                    thread_posts = list(posts[1:])

                thread = await starter.create_thread(
                    name=title[:100],
                    reason="keep-up-with thread",
                )

                for post in thread_posts:
                    files = [_file(path) for path in post.attachments]
                    try:
                        await thread.send(
                            content=post.text or None,
                            files=files or None,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    finally:
                        for file in files:
                            file.close()
                await _add_guild_members_to_thread(parent.guild, thread)
            except discord.HTTPException as error:
                raise ValueError(_discord_error(error)) from error
            return ThreadRef(
                id=str(thread.id),
                name=thread.name,
                channel_id=str(parent.id),
                url=f"https://discord.com/channels/{parent.guild.id}/{thread.id}",
            )

    async def delete_thread(self, *, thread_id: str) -> None:
        async with self._client() as client:
            try:
                target = await client.fetch_channel(int(thread_id))
            except discord.NotFound as error:
                raise ValueError(f"unknown Discord thread: {thread_id}") from error
            if not isinstance(target, discord.Thread):
                raise ValueError(f"not a Discord thread: {thread_id}")
            if client.user is None or target.owner_id != client.user.id:
                raise ValueError("can only delete threads created by keep-up-with")
            starter = await _thread_starter_message(client, target)
            await target.delete()
            if starter is not None and starter.author.id == client.user.id:
                try:
                    await starter.delete()
                except discord.NotFound:
                    pass

    async def list_threads(
        self,
        *,
        channel: str | None = None,
        query: str | None = None,
    ) -> list[ThreadRef]:
        async with self._client() as client:
            guild = await self._guild(client)
            if channel:
                parents = [await self._text_channel(client, channel)]
            else:
                parents = [
                    item
                    for item in await guild.fetch_channels()
                    if isinstance(item, discord.TextChannel)
                ]
            parent_ids = {parent.id for parent in parents}
            threads = [
                thread
                for thread in await guild.active_threads()
                if thread.parent_id in parent_ids
            ]
            for parent in parents:
                try:
                    async for thread in parent.archived_threads(limit=50):
                        threads.append(thread)
                except discord.HTTPException:
                    continue
            unique_threads = {thread.id: thread for thread in threads}
            refs = [
                ThreadRef(
                    id=str(thread.id),
                    name=thread.name,
                    channel_id=str(thread.parent_id or ""),
                    url=f"https://discord.com/channels/{guild.id}/{thread.id}",
                )
                for thread in unique_threads.values()
            ]
            if query:
                needle = query.casefold()
                refs = [ref for ref in refs if needle in ref.name.casefold()]
            return refs

    async def show_thread(self, *, thread_id: str, limit: int) -> dict[str, Any]:
        async with self._client(_message_intents()) as client:
            try:
                channel = await client.fetch_channel(int(thread_id))
            except discord.NotFound as error:
                raise ValueError(f"unknown Discord thread: {thread_id}") from error
            if not isinstance(channel, discord.Thread):
                raise ValueError(f"not a Discord thread: {thread_id}")
            messages = []
            starter = await _thread_starter_message(client, channel)
            if starter is not None:
                messages.append(message_data(starter))
            history = []
            async for message in channel.history(limit=limit):
                if _is_thread_starter_placeholder(message):
                    continue
                history.append(message_data(message))
            messages.extend(reversed(history))
            return {
                "id": str(channel.id),
                "name": channel.name,
                "parent_id": str(channel.parent_id or ""),
                "messages": messages[:limit],
            }

    async def _message_target(
        self,
        client: discord.Client,
        *,
        channel: str | None,
        thread_id: str | None,
    ) -> discord.abc.Messageable:
        if thread_id:
            try:
                target = await client.fetch_channel(int(thread_id))
            except discord.NotFound as error:
                raise ValueError(f"unknown Discord thread: {thread_id}") from error
            if not isinstance(target, discord.abc.Messageable):
                raise ValueError(f"thread is not messageable: {thread_id}")
            return target
        if channel:
            return await self._message_channel(client, channel)
        user = await client.fetch_user(int(self.context.settings()["user_id"]))
        return user.dm_channel or await user.create_dm()

    async def _message_channel(
        self,
        client: discord.Client,
        channel: str,
    ) -> discord.abc.Messageable:
        try:
            return await self._text_channel(client, channel)
        except ValueError as error:
            if not channel.isdigit():
                raise
            user = await client.fetch_user(int(self.context.settings()["user_id"]))
            dm = user.dm_channel or await user.create_dm()
            if str(dm.id) == channel:
                return dm
            raise error

    async def _text_channel(
        self,
        client: discord.Client,
        channel: str,
    ) -> discord.TextChannel:
        if channel.isdigit():
            try:
                target = await client.fetch_channel(int(channel))
            except discord.NotFound as error:
                raise ValueError(f"unknown Discord channel: {channel}") from error
            if isinstance(target, discord.TextChannel):
                return target
            raise ValueError(f"not a Discord text channel: {channel}")

        guild = await self._guild(client)
        channels = await guild.fetch_channels()
        normalized = _normalize_channel_name(channel)
        for target in channels:
            if not isinstance(target, discord.TextChannel):
                continue
            names = {target.name, _normalize_channel_name(target.name)}
            if channel in names or normalized in names:
                return target
        raise ValueError(f"unknown Discord channel: {channel}")

    async def _guild(self, client: discord.Client) -> discord.Guild:
        return await client.fetch_guild(int(self.context.settings()["server_id"]))

    async def _section(
        self,
        guild: discord.Guild,
        section: str | None,
        *,
        create: bool = False,
    ) -> discord.CategoryChannel:
        if not section:
            raise ValueError("section is required")
        if section.isdigit():
            target = await guild.fetch_channel(int(section))
            if isinstance(target, discord.CategoryChannel):
                return target
            raise ValueError(f"not a Discord category: {section}")

        category = _find_section(
            [
                channel
                for channel in await guild.fetch_channels()
                if isinstance(channel, discord.CategoryChannel)
            ],
            section,
        )
        if category is not None:
            return category
        if create:
            return await guild.create_category(
                name=section[:100],
                reason="keep-up-with space management",
            )
        raise ValueError(f"unknown section: {section}")

    async def _create_text_channel(
        self,
        guild: discord.Guild,
        *,
        name: str,
        category: discord.CategoryChannel | None,
        description: str | None,
    ) -> discord.TextChannel:
        return await guild.create_text_channel(
            name=name[:100],
            category=category,
            topic=description[:1024] if description else None,
            reason="keep-up-with space management",
        )


async def _collect_messages(
    target: discord.abc.Messageable,
    *,
    limit: int,
    query: str | None,
    author: str | None,
) -> list[dict[str, Any]]:
    channel_name = getattr(target, "name", None) or "DM"
    messages = []
    async for message in target.history(limit=limit):
        data = message_data(message)
        data["channel_name"] = channel_name
        if query and query.lower() not in data["content"].lower():
            continue
        if author:
            author_filter = author.strip().lower()
            if author_filter not in {
                data["author_id"].lower(),
                data["author_name"].lower(),
            }:
                continue
        messages.append(data)
    return list(reversed(messages))


async def _collect_messages_around(
    target: discord.abc.Messageable,
    anchor: discord.Message,
    *,
    before: int,
    after: int,
) -> list[dict[str, Any]]:
    previous_messages = []
    async for message in target.history(limit=before, before=anchor):
        previous_messages.append(message_data(message))
    next_messages = []
    async for message in target.history(limit=after, after=anchor, oldest_first=True):
        next_messages.append(message_data(message))

    anchor_data = message_data(anchor)
    anchor_data["anchor"] = True
    return [*reversed(previous_messages), anchor_data, *next_messages]


async def _delete_channels(channels: list[Any]) -> None:
    for channel in channels:
        if not isinstance(channel, discord.CategoryChannel):
            await channel.delete(reason="server layout reset")
    for channel in channels:
        if isinstance(channel, discord.CategoryChannel):
            await channel.delete(reason="server layout reset")


def _space_delete_items(channels: list[Any]) -> list[SpaceDeleteItem]:
    items = []
    for channel in channels:
        if isinstance(channel, discord.CategoryChannel):
            items.append(SpaceDeleteItem(kind="section", name=channel.name))
        elif isinstance(channel, discord.TextChannel):
            items.append(
                SpaceDeleteItem(
                    kind="text channel",
                    name=f"#{channel.name}",
                )
            )
        elif isinstance(channel, discord.VoiceChannel):
            items.append(SpaceDeleteItem(kind="voice channel", name=channel.name))
        else:
            items.append(
                SpaceDeleteItem(
                    kind=str(getattr(channel, "type", "channel")),
                    name=str(getattr(channel, "name", channel.id)),
                )
            )
    return items


async def _default_empty_server(channels: list[Any]) -> bool:
    # This detects Discord's English default template. Other locales fall back
    # to the explicit reset confirmation path.
    if len(channels) != 4:
        return False
    sections = [
        channel for channel in channels if isinstance(channel, discord.CategoryChannel)
    ]
    text_channels = [
        channel for channel in channels if isinstance(channel, discord.TextChannel)
    ]
    voice_channels = [
        channel for channel in channels if isinstance(channel, discord.VoiceChannel)
    ]
    if {section.name for section in sections} != {"Text Channels", "Voice Channels"}:
        return False
    if len(text_channels) != 1 or len(voice_channels) != 1:
        return False
    text_channel = text_channels[0]
    voice_channel = voice_channels[0]
    sections_by_id = _sections_by_id(channels)
    return bool(
        text_channel.name == "general"
        and sections_by_id.get(text_channel.category_id)
        and sections_by_id[text_channel.category_id].name == "Text Channels"
        and not await _has_messages(text_channel)
        and voice_channel.name == "General"
        and sections_by_id.get(voice_channel.category_id)
        and sections_by_id[voice_channel.category_id].name == "Voice Channels"
    )


async def _has_messages(channel: discord.TextChannel) -> bool:
    try:
        async for _message in channel.history(limit=1):
            return True
    except discord.HTTPException:
        return True
    return False


def _find_section(
    sections: list[discord.CategoryChannel],
    name: str,
) -> discord.CategoryChannel | None:
    normalized = _normalize_channel_name(name)
    for section in sections:
        if name.isdigit() and str(section.id) == name:
            return section
        if name in {section.name, _normalize_channel_name(section.name)}:
            return section
        if normalized == _normalize_channel_name(section.name):
            return section
    return None


def _sections_by_id(channels: list[Any]) -> dict[int, discord.CategoryChannel]:
    return {
        channel.id: channel
        for channel in channels
        if isinstance(channel, discord.CategoryChannel)
    }


def _find_text_channel(
    channels: list[discord.TextChannel],
    name: str,
    *,
    category: discord.CategoryChannel | None = None,
) -> discord.TextChannel | None:
    normalized = _normalize_channel_name(name)
    for channel in channels:
        if category is not None and channel.category_id != category.id:
            continue
        if name.isdigit() and str(channel.id) == name:
            return channel
        if name in {channel.name, _normalize_channel_name(channel.name)}:
            return channel
        if normalized == _normalize_channel_name(channel.name):
            return channel
    return None


async def _fetch_message(channel: discord.abc.Messageable, message_id: str) -> Any:
    fetch = getattr(channel, "fetch_message", None)
    if not callable(fetch):
        raise ValueError("channel does not support message lookup")
    try:
        return await fetch(int(message_id))
    except discord.NotFound as error:
        raise ValueError(f"unknown message: {message_id}") from error


async def _own_message(
    client: discord.Client,
    channel: discord.abc.Messageable,
    message_id: str,
) -> discord.Message:
    message = await _fetch_message(channel, message_id)
    if client.user is None or message.author.id != client.user.id:
        raise ValueError("can only edit or delete keep-up-with's own messages")
    return message


async def _thread_starter_message(
    client: discord.Client,
    thread: discord.Thread,
) -> discord.Message | None:
    if thread.parent_id is None:
        return None
    try:
        parent = await client.fetch_channel(thread.parent_id)
    except (discord.Forbidden, discord.NotFound):
        return None
    fetch = getattr(parent, "fetch_message", None)
    if not callable(fetch):
        return None
    try:
        return await fetch(thread.id)
    except (discord.Forbidden, discord.NotFound):
        return None


def _is_thread_starter_placeholder(message: discord.Message) -> bool:
    return getattr(message.type, "name", "") == "thread_starter_message"


def _message_ref(message: discord.Message) -> MessageRef:
    return MessageRef(
        channel_id=str(message.channel.id),
        thread_id=str(message.channel.id) if isinstance(message.channel, discord.Thread) else None,
        message_id=str(message.id),
        url=message.jump_url,
    )


def _channel_ref(
    channel: discord.TextChannel,
    sections_by_id: dict[int, discord.CategoryChannel] | None = None,
    category: discord.CategoryChannel | None = None,
) -> ChannelRef:
    category_id = channel.category_id
    category = category or (
        sections_by_id.get(category_id) if sections_by_id and category_id else None
    )
    category = category or channel.category
    return ChannelRef(
        id=str(channel.id),
        name=channel.name,
        type="text",
        description=channel.topic or "",
        section=category.name if category else "",
        section_id=str(category_id or ""),
        position=channel.position,
    )


def _section_ref(section: discord.CategoryChannel) -> SectionRef:
    return SectionRef(
        id=str(section.id),
        name=section.name,
        position=section.position,
    )


async def _add_guild_members_to_thread(
    guild: discord.Guild,
    thread: discord.Thread,
) -> None:
    try:
        mentions: list[str] = []
        async for member in guild.fetch_members(limit=None):
            if member.bot:
                continue
            mentions.append(member.mention)
        for chunk in _mention_chunks(mentions):
            try:
                message = await thread.send(
                    "\u200b",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                await message.edit(
                    content=chunk,
                    allowed_mentions=discord.AllowedMentions(
                        everyone=False,
                        users=True,
                        roles=False,
                        replied_user=False,
                    ),
                )
            except discord.HTTPException:
                continue
    except (discord.ClientException, discord.HTTPException):
        return


def _mention_chunks(mentions: list[str]) -> list[str]:
    chunks: list[str] = []
    current = ""
    for mention in mentions:
        candidate = f"{current} {mention}".strip()
        if len(candidate) > DISCORD_MESSAGE_LIMIT:
            if current:
                chunks.append(current)
            current = mention
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _validate_message_text(text: str) -> None:
    if len(text) > DISCORD_MESSAGE_LIMIT:
        raise ValueError(
            "message text is "
            f"{len(text)} characters; Discord allows {DISCORD_MESSAGE_LIMIT}. "
            "Split it into shorter messages or thread posts before sending."
        )


def _discord_error(error: discord.HTTPException) -> str:
    detail = getattr(error, "text", "") or str(error)
    if "2000" in detail or "Must be 2000 or fewer" in detail:
        return (
            f"message text exceeded Discord's {DISCORD_MESSAGE_LIMIT}-character "
            "limit; split it into shorter messages or thread posts before sending"
        )
    return f"Discord send failed: {detail}"


def _file(path: str) -> discord.File:
    return discord.File(str(Path(path).expanduser()))


def _message_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    return intents


def _thread_member_intents() -> discord.Intents:
    intents = discord.Intents.none()
    intents.members = True
    return intents


def _normalize_channel_name(value: str) -> str:
    value = value.strip().lower()
    if "・" in value:
        value = value.split("・", 1)[1]
    return value.replace(" ", "-")

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

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


class FileMessagingClient:
    def __init__(self, context: MessagingContext) -> None:
        self.context = context
        self.root = Path(
            context.settings().get("output_dir")
            or context._config.paths.home / "output"  # noqa: SLF001
        )
        self.state_dir = context._config.paths.run / "file-messaging"  # noqa: SLF001
        self.state_path = self.state_dir / "state.json"

    async def list_channels(self) -> list[ChannelRef]:
        state = self._state()
        return [
            ChannelRef(
                id=row["id"],
                name=row["name"],
                type="text",
                description=row.get("description", ""),
                section=row.get("section", ""),
                section_id=row.get("section_id", ""),
                position=int(row.get("position", 0)),
            )
            for row in sorted(state["channels"], key=lambda item: item["position"])
        ]

    async def list_sections(self) -> list[SectionRef]:
        state = self._state()
        return [
            SectionRef(
                id=row["id"],
                name=row["name"],
                position=int(row.get("position", 0)),
            )
            for row in sorted(state["sections"], key=lambda item: item["position"])
        ]

    async def apply_space(self, plan: SpacePlan, *, reset: bool = False) -> None:
        state = self._state()
        if reset:
            state["sections"] = []
            state["channels"] = []
            state["messages"] = {"dm": []}
            state["threads"] = []
        for index, section in enumerate(plan.sections):
            current = self._find_section(state, section.key, required=False)
            row = {
                "id": section.key,
                "name": section.name,
                "position": index,
            }
            if current is None:
                state["sections"].append(row)
            else:
                current.update(row)
        for index, channel in enumerate(plan.channels):
            current = self._find_channel(state, channel.key, required=False)
            row = {
                "id": channel.key,
                "name": channel.name,
                "description": channel.description,
                "section": channel.section,
                "section_id": channel.section,
                "position": index,
            }
            if current is None:
                state["channels"].append(row)
            else:
                current.update(row)
            state["messages"].setdefault(channel.key, [])
        self._save(state)

    async def preview_space_reset(self) -> SpaceResetPreview:
        state = self._state()
        items = [
            *(SpaceDeleteItem("section", row["name"]) for row in state["sections"]),
            *(SpaceDeleteItem("text channel", row["name"]) for row in state["channels"]),
        ]
        return SpaceResetPreview(
            items=tuple(items),
            default_empty_server=not items,
            target=f"file message space: {self.root}",
        )

    async def create_channel(
        self,
        *,
        name: str,
        section: str | None = None,
        description: str | None = None,
    ) -> ChannelRef:
        state = self._state()
        section_row = self._find_section(state, section, required=False) if section else None
        channel_id = unique_id(state, "channel", slug(name))
        row = {
            "id": channel_id,
            "name": name,
            "description": description or "",
            "section": section_row["name"] if section_row else "",
            "section_id": section_row["id"] if section_row else "",
            "position": len(state["channels"]),
        }
        state["channels"].append(row)
        state["messages"].setdefault(channel_id, [])
        self._save(state)
        return ChannelRef(
            id=row["id"],
            name=row["name"],
            type="text",
            description=row["description"],
            section=row["section"],
            section_id=row["section_id"],
            position=row["position"],
        )

    async def rename_channel(self, *, channel: str, name: str) -> ChannelRef:
        state = self._state()
        row = self._find_channel(state, channel)
        row["name"] = name
        self._save(state)
        return ChannelRef(
            id=row["id"],
            name=row["name"],
            type="text",
            description=row.get("description", ""),
            section=row.get("section", ""),
            section_id=row.get("section_id", ""),
            position=int(row.get("position", 0)),
        )

    async def move_channel(
        self,
        *,
        channel: str,
        section: str | None = None,
        before: str | None = None,
        after: str | None = None,
    ) -> ChannelRef:
        state = self._state()
        row = self._find_channel(state, channel)
        if section:
            section_row = self._find_section(state, section)
            row["section"] = section_row["name"]
            row["section_id"] = section_row["id"]
        if before or after:
            anchor = self._find_channel(state, before or after or "")
            row["position"] = int(anchor.get("position", 0)) + (1 if after else 0)
        self._normalize_positions(state["channels"])
        self._save(state)
        return ChannelRef(
            id=row["id"],
            name=row["name"],
            type="text",
            description=row.get("description", ""),
            section=row.get("section", ""),
            section_id=row.get("section_id", ""),
            position=int(row.get("position", 0)),
        )

    async def create_section(self, *, name: str) -> SectionRef:
        state = self._state()
        section_id = unique_id(state, "section", slug(name))
        row = {"id": section_id, "name": name, "position": len(state["sections"])}
        state["sections"].append(row)
        self._save(state)
        return SectionRef(id=row["id"], name=row["name"], position=row["position"])

    async def rename_section(self, *, section: str, name: str) -> SectionRef:
        state = self._state()
        row = self._find_section(state, section)
        row["name"] = name
        for channel in state["channels"]:
            if channel.get("section_id") == row["id"]:
                channel["section"] = name
        self._save(state)
        return SectionRef(id=row["id"], name=row["name"], position=row["position"])

    async def move_section(
        self,
        *,
        section: str,
        before: str | None = None,
        after: str | None = None,
    ) -> SectionRef:
        state = self._state()
        row = self._find_section(state, section)
        anchor = self._find_section(state, before or after or "")
        row["position"] = int(anchor.get("position", 0)) + (1 if after else 0)
        self._normalize_positions(state["sections"])
        self._save(state)
        return SectionRef(id=row["id"], name=row["name"], position=row["position"])

    async def list_messages(
        self,
        *,
        channel: str | None = None,
        thread_id: str | None = None,
        limit: int = 25,
        query: str | None = None,
        author: str | None = None,
    ) -> list[dict[str, Any]]:
        state = self._state()
        if thread_id:
            rows = self._thread_messages(state, thread_id)
        elif channel:
            channel_row = self._find_channel(state, channel)
            rows = state["messages"].get(channel_row["id"], [])
        elif query:
            rows = [
                row
                for messages in state["messages"].values()
                for row in messages
            ]
        else:
            rows = state["messages"].get("dm", [])
        rows = list(rows)
        if query:
            needle = query.casefold()
            rows = [row for row in rows if needle in row.get("text", "").casefold()]
        if author:
            rows = [
                row for row in rows
                if author in {row.get("author", ""), row.get("author_id", "")}
            ]
        rows = rows[-max(1, min(limit, 100)):]
        return [self._message_output(row) for row in rows]

    async def messages_around(
        self,
        *,
        message_id: str,
        channel: str | None = None,
        thread_id: str | None = None,
        before: int = 10,
        after: int = 20,
    ) -> list[dict[str, Any]]:
        state = self._state()
        if thread_id:
            rows = self._thread_messages(state, thread_id)
        elif channel:
            channel_row = self._find_channel(state, channel)
            rows = state["messages"].get(channel_row["id"], [])
        else:
            rows = [
                row
                for messages in state["messages"].values()
                for row in messages
            ]
            rows += [row for thread in state["threads"] for row in thread["messages"]]
        index = next(
            (idx for idx, row in enumerate(rows) if row["id"] == message_id),
            None,
        )
        if index is None:
            raise ValueError(f"unknown message: {message_id}")
        start = max(0, index - max(0, before))
        end = index + max(0, after) + 1
        return [self._message_output(row) for row in rows[start:end]]

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
        state = self._state()
        message = self._new_message(
            state,
            text=text,
            attachments=attachments or [],
            reply_to=reply_to,
        )
        if thread_id:
            thread = self._find_thread(state, thread_id)
            message["thread_id"] = thread["id"]
            message["channel_id"] = thread["channel_id"]
            thread["messages"].append(message)
        elif channel:
            channel_row = self._find_channel(state, channel)
            message["channel_id"] = channel_row["id"]
            state["messages"].setdefault(channel_row["id"], []).append(message)
        else:
            message["channel_id"] = "dm"
            state["messages"].setdefault("dm", []).append(message)
        self._save(state)
        return MessageRef(
            channel_id=message["channel_id"],
            message_id=message["id"],
            thread_id=message.get("thread_id"),
            url=message["url"],
        )

    async def edit_message(
        self,
        *,
        message_id: str,
        text: str,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> MessageRef:
        state = self._state()
        message = self._find_message(state, message_id, channel=channel, thread_id=thread_id)
        message["text"] = text
        message["edited_at"] = now()
        self._save(state)
        return MessageRef(
            channel_id=message["channel_id"],
            message_id=message["id"],
            thread_id=message.get("thread_id"),
            url=message["url"],
        )

    async def delete_message(
        self,
        *,
        message_id: str,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        state = self._state()
        removed = self._delete_message(state, message_id, channel=channel, thread_id=thread_id)
        if not removed:
            raise ValueError(f"unknown message: {message_id}")
        self._save(state)

    async def create_thread(
        self,
        *,
        channel: str,
        title: str,
        posts: Sequence[ThreadPost],
        from_message: str | None = None,
    ) -> ThreadRef:
        if not posts:
            raise ValueError("at least one post is required")
        state = self._state()
        channel_row = self._find_channel(state, channel)
        thread_id = next_id(state, "thread", "thread")
        thread = {
            "id": thread_id,
            "name": title,
            "channel_id": channel_row["id"],
            "created_at": now(),
            "url": f"file://thread/{thread_id}",
            "messages": [],
        }
        if from_message:
            starter = self._find_channel_message(state, channel_row["id"], from_message)
            if starter.get("thread_id"):
                raise ValueError(
                    f"message already has a thread: {starter['thread_id']}; use thread append"
                )
            starter["thread_id"] = thread_id
            opener = dict(starter)
            opener["thread_id"] = thread_id
            thread["messages"].append(opener)
            thread_posts = list(posts)
        else:
            first = posts[0]
            starter = self._new_message(
                state,
                text=first.text,
                attachments=list(first.attachments),
            )
            starter["channel_id"] = channel_row["id"]
            starter["thread_id"] = thread_id
            state["messages"].setdefault(channel_row["id"], []).append(starter)
            thread["messages"].append(dict(starter))
            thread_posts = list(posts[1:])

        state["threads"].append(thread)
        starter["thread_link"] = {
            "id": thread["id"],
            "name": thread["name"],
            "path": f"../threads/{thread['id']}.md",
        }
        for post in thread_posts:
            message = self._new_message(
                state,
                text=post.text,
                attachments=list(post.attachments),
            )
            message["channel_id"] = channel_row["id"]
            message["thread_id"] = thread_id
            thread["messages"].append(message)
        message = self._new_message(state, text="@everyone", attachments=[])
        message["channel_id"] = channel_row["id"]
        message["thread_id"] = thread_id
        thread["messages"].append(message)
        self._save(state)
        return ThreadRef(
            id=thread["id"],
            name=thread["name"],
            channel_id=channel_row["id"],
            url=thread["url"],
        )

    async def delete_thread(self, *, thread_id: str) -> None:
        state = self._state()
        before = len(state["threads"])
        state["threads"] = [
            thread for thread in state["threads"]
            if thread["id"] != thread_id
        ]
        if len(state["threads"]) == before:
            raise ValueError(f"unknown thread: {thread_id}")
        for messages in state["messages"].values():
            for message in messages:
                if message.get("thread_id") == thread_id:
                    message.pop("thread_id", None)
                    message.pop("thread_link", None)
        self._save(state)

    async def list_threads(
        self,
        *,
        channel: str | None = None,
        query: str | None = None,
    ) -> list[ThreadRef]:
        state = self._state()
        channel_id = self._find_channel(state, channel)["id"] if channel else None
        rows = state["threads"]
        if channel_id:
            rows = [row for row in rows if row["channel_id"] == channel_id]
        if query:
            needle = query.casefold()
            rows = [row for row in rows if needle in row["name"].casefold()]
        return [
            ThreadRef(
                id=row["id"],
                name=row["name"],
                channel_id=row["channel_id"],
                url=row["url"],
            )
            for row in rows
        ]

    async def show_thread(self, *, thread_id: str, limit: int) -> dict[str, Any]:
        state = self._state()
        thread = self._find_thread(state, thread_id)
        messages = thread["messages"][-max(1, min(limit, 100)):]
        return {
            "id": thread["id"],
            "name": thread["name"],
            "channel_id": thread["channel_id"],
            "url": thread["url"],
            "messages": [self._message_output(row) for row in messages],
        }

    def _state(self) -> dict[str, Any]:
        try:
            data = json.loads(self.state_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "counters": {},
                "sections": [],
                "channels": [],
                "messages": {"dm": []},
                "threads": [],
            }
        data.setdefault("counters", {})
        data.setdefault("sections", [])
        data.setdefault("channels", [])
        data.setdefault("messages", {"dm": []})
        data.setdefault("threads", [])
        return data

    def _save(self, state: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        render_output(self.root, state)

    def _new_message(
        self,
        state: dict[str, Any],
        *,
        text: str,
        attachments: list[str],
        reply_to: str | None = None,
    ) -> dict[str, Any]:
        message_id = next_id(state, "message", "msg")
        copied = [self._copy_attachment(path, message_id, index) for index, path in enumerate(attachments, start=1)]
        return {
            "id": message_id,
            "author": "keep-up-with",
            "author_id": "keep-up-with",
            "text": text,
            "attachments": copied,
            "reply_to": reply_to,
            "created_at": now(),
            "url": f"file://message/{message_id}",
        }

    def _copy_attachment(self, path: str, message_id: str, index: int) -> dict[str, str]:
        source = Path(path).expanduser()
        if not source.exists():
            return {"source": path, "path": path, "missing": "true"}
        attachments = self.root / "attachments"
        attachments.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix or ".bin"
        name = f"{message_id}-{index}{suffix}"
        target = attachments / name
        shutil.copy2(source, target)
        return {"source": str(source), "path": f"attachments/{name}"}

    def _find_section(
        self,
        state: dict[str, Any],
        value: str | None,
        *,
        required: bool = True,
    ) -> dict[str, Any] | None:
        if not value:
            if required:
                raise ValueError("section is required")
            return None
        for row in state["sections"]:
            if value in {row["id"], row["name"]}:
                return row
        if required:
            raise ValueError(f"unknown section: {value}")
        return None

    def _find_channel(
        self,
        state: dict[str, Any],
        value: str | None,
        *,
        required: bool = True,
    ) -> dict[str, Any] | None:
        if not value:
            if required:
                raise ValueError("channel is required")
            return None
        normalized = normalize_channel(value)
        for row in state["channels"]:
            if (
                value in {row["id"], row["name"]}
                or normalized in channel_aliases(row)
            ):
                return row
        if required:
            raise ValueError(f"unknown channel: {value}")
        return None

    def _find_thread(self, state: dict[str, Any], thread_id: str) -> dict[str, Any]:
        for row in state["threads"]:
            if row["id"] == thread_id or row["name"] == thread_id:
                return row
        raise ValueError(f"unknown thread: {thread_id}")

    def _thread_messages(self, state: dict[str, Any], thread_id: str) -> list[dict[str, Any]]:
        return list(self._find_thread(state, thread_id)["messages"])

    def _find_message(
        self,
        state: dict[str, Any],
        message_id: str,
        *,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        if thread_id:
            rows = self._thread_messages(state, thread_id)
        elif channel:
            channel_id = self._find_channel(state, channel)["id"]  # type: ignore[index]
            rows = state["messages"].get(channel_id, [])
        else:
            rows = [
                row
                for messages in state["messages"].values()
                for row in messages
            ]
            rows += [row for thread in state["threads"] for row in thread["messages"]]
        for row in rows:
            if row["id"] == message_id:
                return row
        raise ValueError(f"unknown message: {message_id}")

    def _find_channel_message(
        self,
        state: dict[str, Any],
        channel_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        for row in state["messages"].get(channel_id, []):
            if row["id"] == message_id:
                return row
        for thread in state["threads"]:
            for row in thread["messages"]:
                if row["id"] == message_id:
                    raise ValueError("cannot create a thread from a thread message; use thread append")
        raise ValueError(f"unknown message: {message_id}")

    def _delete_message(
        self,
        state: dict[str, Any],
        message_id: str,
        *,
        channel: str | None,
        thread_id: str | None,
    ) -> bool:
        containers: list[list[dict[str, Any]]]
        if thread_id:
            containers = [self._find_thread(state, thread_id)["messages"]]
        elif channel:
            channel_id = self._find_channel(state, channel)["id"]  # type: ignore[index]
            containers = [state["messages"].get(channel_id, [])]
        else:
            containers = list(state["messages"].values())
            containers += [thread["messages"] for thread in state["threads"]]
        for rows in containers:
            for index, row in enumerate(rows):
                if row["id"] == message_id:
                    rows.pop(index)
                    return True
        return False

    def _message_output(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "author": row.get("author", "keep-up-with"),
            "author_id": row.get("author_id", "keep-up-with"),
            "text": row.get("text", ""),
            "attachments": row.get("attachments", []),
            "reply_to": row.get("reply_to"),
            "channel_id": row.get("channel_id"),
            "thread_id": row.get("thread_id"),
            "url": row.get("url", ""),
            "created_at": row.get("created_at", ""),
        }

    def _normalize_positions(self, rows: list[dict[str, Any]]) -> None:
        for index, row in enumerate(sorted(rows, key=lambda item: item.get("position", 0))):
            row["position"] = index


def render_output(root: Path, state: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "channels").mkdir(parents=True, exist_ok=True)
    (root / "threads").mkdir(parents=True, exist_ok=True)
    write_markdown(
        root / "dm.md",
        "# DM\n\n" + render_messages(
            state["messages"].get("dm", []),
            attachment_prefix="",
        ),
    )
    for channel in state["channels"]:
        messages = state["messages"].get(channel["id"], [])
        text = f"# {channel['name']}\n\n"
        if channel.get("description"):
            text += f"{channel['description']}\n\n"
        text += render_messages(messages, attachment_prefix="../")
        write_markdown(root / "channels" / f"{channel['id']}.md", text)
    for thread in state["threads"]:
        channel = next(
            (row for row in state["channels"] if row["id"] == thread["channel_id"]),
            None,
        )
        text = f"# {thread['name']}\n\n"
        if channel:
            text += f"Channel: [{channel['name']}](../channels/{channel['id']}.md)\n\n"
        text += render_messages(thread["messages"], attachment_prefix="../")
        write_markdown(root / "threads" / f"{thread['id']}.md", text)


def render_messages(
    messages: list[dict[str, Any]],
    *,
    attachment_prefix: str,
) -> str:
    if not messages:
        return "_No messages._\n"
    parts: list[str] = []
    for row in messages:
        timestamp = row.get("created_at", "")
        parts.append(f"## {row['id']} · {row.get('author', 'keep-up-with')} · {timestamp}")
        if row.get("reply_to"):
            parts.append(f"\nReply to: `{row['reply_to']}`")
        text = row.get("text", "")
        if text:
            parts.append(f"\n{text}")
        for attachment in row.get("attachments", []):
            path = attachment.get("path", "")
            if not path:
                continue
            alt = Path(path).name
            prefix = attachment_prefix if path.startswith("attachments/") else ""
            if image_like(path):
                parts.append(f"\n![{alt}]({prefix}{path})")
            else:
                parts.append(f"\n[{alt}]({prefix}{path})")
        link = row.get("thread_link")
        if link:
            parts.append(f"\n[Thread: {link['name']}]({link['path']})")
        parts.append("")
    return "\n\n".join(parts).rstrip() + "\n"


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def image_like(path: str) -> bool:
    return Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def next_id(state: dict[str, Any], key: str, prefix: str) -> str:
    value = int(state["counters"].get(key, 0)) + 1
    state["counters"][key] = value
    return f"{prefix}_{value:04d}"


def unique_id(state: dict[str, Any], kind: str, base: str) -> str:
    existing = {row["id"] for row in state[f"{kind}s"]}
    candidate = base or kind
    if candidate not in existing:
        return candidate
    index = 2
    while f"{candidate}-{index}" in existing:
        index += 1
    return f"{candidate}-{index}"


def now() -> str:
    return datetime.now(UTC).isoformat()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.casefold()).strip("-")
    return cleaned or "item"


def normalize_channel(value: str) -> str:
    return value.removeprefix("#").strip().casefold()


def channel_aliases(row: dict[str, Any]) -> set[str]:
    name = str(row.get("name") or "")
    channel_id = str(row.get("id") or "")
    aliases = {normalize_channel(name), normalize_channel(channel_id)}
    if "." in channel_id:
        aliases.add(normalize_channel(channel_id.rsplit(".", 1)[-1]))
    if "・" in name:
        aliases.add(normalize_channel(name.rsplit("・", 1)[-1]))
    return aliases

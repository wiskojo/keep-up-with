from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl, fail
from keep_up_with.core.config import get_config
from keep_up_with.integrations.base import ThreadPost
from keep_up_with.integrations.registry import messaging_client

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Create and update threads",
    no_args_is_help=True,
)

POST_HEADING_RE = re.compile(r"^##\s.*\n?", re.MULTILINE)
ATTACHMENT_LINE_RE = re.compile(r"^attachment:\s*(.+)$", re.IGNORECASE)


@app.command("create", help="Create a thread and publish all of its posts at once")
def create_command(
    channel: Annotated[str, typer.Option(help="Channel name or id")],
    title: Annotated[str, typer.Option(help="Thread title")],
    file: Annotated[
        str | None,
        typer.Option(
            "--file",
            "-f",
            help="Markdown draft to publish: each '## ' heading starts a post; 'Attachment: <path>' lines attach files to their post",
        ),
    ] = None,
    post: Annotated[
        list[str] | None,
        typer.Option("--post", "-p", help="Post text, repeat once per post in order"),
    ] = None,
    attachment: Annotated[
        list[str] | None,
        typer.Option(
            "--attachment",
            "-a",
            help="File to attach: a path attaches to post 1, N:path to post N",
        ),
    ] = None,
    from_message: Annotated[
        str | None,
        typer.Option(
            "--from-message",
            help="Convert an existing channel message into the thread opener; every post then goes inside the thread",
        ),
    ] = None,
) -> None:
    if file and (post or attachment):
        fail("use --file or --post/--attachment, not both")
    if file:
        posts = parse_posts_file(file)
    elif post:
        posts = build_posts(post, attachment or [])
    else:
        fail("provide --file or at least one --post")
    client = messaging_client(get_config())
    try:
        thread = asyncio.run(
            client.create_thread(
                channel=channel,
                title=title,
                posts=posts,
                from_message=from_message,
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json(thread)


def parse_posts_file(path: str) -> list[ThreadPost]:
    try:
        text = Path(path).expanduser().read_text()
    except OSError as error:
        fail(f"could not read posts file: {error}")
    posts: list[ThreadPost] = []
    for section in POST_HEADING_RE.split(text)[1:]:
        attachments: list[str] = []
        lines: list[str] = []
        for line in section.splitlines():
            match = ATTACHMENT_LINE_RE.match(line.strip())
            if match:
                attachments.append(match.group(1).strip())
            else:
                lines.append(line)
        body = "\n".join(lines).strip()
        if body or attachments:
            posts.append(ThreadPost(text=body, attachments=tuple(attachments)))
    if not posts:
        fail(f"no posts found in {path}; start each post with a '## ' heading")
    return posts


def build_posts(texts: list[str], attachments: list[str]) -> list[ThreadPost]:
    by_post: dict[int, list[str]] = {}
    for item in attachments:
        prefix, separator, rest = item.partition(":")
        if separator and prefix.isdigit():
            index, path = int(prefix), rest
        else:
            index, path = 1, item
        if not path or not 1 <= index <= len(texts):
            fail(f"attachment does not match a post: {item}")
        by_post.setdefault(index, []).append(path)
    return [
        ThreadPost(text=text, attachments=tuple(by_post.get(index, ())))
        for index, text in enumerate(texts, start=1)
    ]


@app.command("append", help="Append a message to a thread")
def append_command(
    thread_id: Annotated[str, typer.Argument(help="Thread id")],
    text: Annotated[str, typer.Option("--text", "-t", help="Message text")] = "",
    attachment: Annotated[
        list[str] | None,
        typer.Option(
            "--attachment",
            "-a",
            help="File path to attach, repeat for multiple files",
        ),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        message = asyncio.run(
            client.send_message(
                thread_id=thread_id,
                text=text,
                attachments=attachment or [],
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json(message)


@app.command("delete", help="Delete a thread created by keep-up-with")
def delete_command(
    thread_id: Annotated[str, typer.Argument(help="Thread id")],
) -> None:
    client = messaging_client(get_config())
    try:
        asyncio.run(client.delete_thread(thread_id=thread_id))
    except ValueError as error:
        fail(str(error))
    echo_json({"deleted": True, "id": thread_id})


@app.command("list", help="List threads, searching all channels unless --channel is given")
def list_command(
    channel: Annotated[str | None, typer.Option(help="Channel name or id")] = None,
    query: Annotated[
        str | None,
        typer.Option("--query", "-q", help="Only include threads whose title contains text"),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        threads = asyncio.run(client.list_threads(channel=channel, query=query))
    except ValueError as error:
        fail(str(error))
    echo_jsonl(threads)


@app.command("show", help="Show a thread and recent messages")
def show_command(
    thread_id: Annotated[str, typer.Argument(help="Thread id")],
    limit: Annotated[int, typer.Option(help="Maximum messages")] = 25,
) -> None:
    client = messaging_client(get_config())
    try:
        thread = asyncio.run(client.show_thread(thread_id=thread_id, limit=limit))
    except ValueError as error:
        fail(str(error))
    echo_json(thread)

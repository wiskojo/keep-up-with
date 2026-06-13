from __future__ import annotations

import asyncio
from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl, fail
from keep_up_with.core.config import get_config
from keep_up_with.integrations.registry import messaging_client

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Send and list messages",
    no_args_is_help=True,
)


@app.command("send", help="Send a message to a channel or the DM (default); use `thread append` for threads")
def send_command(
    text: Annotated[str, typer.Option("--text", "-t", help="Message text")] = "",
    channel: Annotated[str | None, typer.Option(help="Channel name or id")] = None,
    reply_to: Annotated[str | None, typer.Option(help="Message id to reply to")] = None,
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
        result = asyncio.run(
            client.send_message(
                text=text,
                channel=channel,
                reply_to=reply_to,
                attachments=attachment or [],
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json(result)


@app.command("list", help="List recent messages, defaults to DM")
def list_command(
    channel: Annotated[str | None, typer.Option(help="Channel name or id")] = None,
    thread_id: Annotated[str | None, typer.Option(help="Thread id")] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum recent messages to scan per channel"),
    ] = 25,
    query: Annotated[
        str | None,
        typer.Option(
            "--query",
            "-q",
            help="Only include messages containing text; without --channel this searches every channel and the DM",
        ),
    ] = None,
    author: Annotated[
        str | None,
        typer.Option(help="Only include messages by author id or exact name"),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        messages = asyncio.run(
            client.list_messages(
                channel=channel,
                thread_id=thread_id,
                limit=limit,
                query=query,
                author=author,
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_jsonl(messages)


@app.command("around", help="Show messages around a message")
def around_command(
    message_id: Annotated[str, typer.Argument(help="Message id")],
    channel: Annotated[str | None, typer.Option(help="Channel name or id")] = None,
    thread_id: Annotated[str | None, typer.Option(help="Thread id")] = None,
    before: Annotated[int, typer.Option(help="Messages before the target")] = 10,
    after: Annotated[int, typer.Option(help="Messages after the target")] = 20,
) -> None:
    client = messaging_client(get_config())
    try:
        messages = asyncio.run(
            client.messages_around(
                message_id=message_id,
                channel=channel,
                thread_id=thread_id,
                before=before,
                after=after,
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_jsonl(messages)


@app.command("edit", help="Edit one of keep-up-with's own messages")
def edit_command(
    message_id: Annotated[str, typer.Argument(help="Message id")],
    text: Annotated[str, typer.Option("--text", "-t", help="Replacement text")],
    channel: Annotated[str | None, typer.Option(help="Channel name or id")] = None,
    thread_id: Annotated[str | None, typer.Option(help="Thread id")] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        result = asyncio.run(
            client.edit_message(
                message_id=message_id,
                text=text,
                channel=channel,
                thread_id=thread_id,
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json(result)


@app.command("delete", help="Delete one of keep-up-with's own messages")
def delete_command(
    message_id: Annotated[str, typer.Argument(help="Message id")],
    channel: Annotated[str | None, typer.Option(help="Channel name or id")] = None,
    thread_id: Annotated[str | None, typer.Option(help="Thread id")] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        asyncio.run(
            client.delete_message(
                message_id=message_id,
                channel=channel,
                thread_id=thread_id,
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json({"deleted": True, "id": message_id})

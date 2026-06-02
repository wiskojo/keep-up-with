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
    help="Create and update story threads.",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("create", help="Create a thread in a channel.")
def create_command(
    channel: Annotated[str, typer.Option(help="Channel name or id.")],
    title: Annotated[str, typer.Option(help="Thread title.")],
    text: Annotated[str, typer.Option("--text", "-t", help="Initial message text.")] = "",
    attachment: Annotated[
        list[str] | None,
        typer.Option(
            "--attachment",
            "-a",
            help="File path to attach. Repeat for multiple files.",
        ),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        thread = asyncio.run(
            client.create_thread(
                channel=channel,
                title=title,
                text=text,
                attachments=attachment or [],
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json(thread)


@app.command("append", help="Append a message to a thread.")
def append_command(
    thread_id: Annotated[str, typer.Option(help="Thread id.")],
    text: Annotated[str, typer.Option("--text", "-t", help="Message text.")] = "",
    attachment: Annotated[
        list[str] | None,
        typer.Option(
            "--attachment",
            "-a",
            help="File path to attach. Repeat for multiple files.",
        ),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    try:
        message = asyncio.run(
            client.append_thread(
                thread_id=thread_id,
                text=text,
                attachments=attachment or [],
            )
        )
    except ValueError as error:
        fail(str(error))
    echo_json(message)


@app.command("list", help="List threads in a channel.")
def list_command(
    channel: Annotated[str, typer.Option(help="Channel name or id.")],
) -> None:
    client = messaging_client(get_config())
    try:
        threads = asyncio.run(client.list_threads(channel=channel))
    except ValueError as error:
        fail(str(error))
    echo_jsonl(threads)


@app.command("show", help="Show a thread and recent messages.")
def show_command(
    thread_id: Annotated[str, typer.Argument(help="Thread id.")],
    limit: Annotated[int, typer.Option(help="Maximum messages.")] = 25,
) -> None:
    client = messaging_client(get_config())
    try:
        thread = asyncio.run(client.show_thread(thread_id=thread_id, limit=limit))
    except ValueError as error:
        fail(str(error))
    echo_json(thread)

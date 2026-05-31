from __future__ import annotations

import asyncio
from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl
from keep_up_with.core.config import get_config
from keep_up_with.integrations.registry import messaging_client

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Send and read messages.",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("send", help="Send a message. Defaults to DM.")
def send_command(
    text: Annotated[str, typer.Option("--text", "-t", help="Message text.")] = "",
    channel: Annotated[str | None, typer.Option(help="Channel name or id.")] = None,
    thread_id: Annotated[str | None, typer.Option(help="Thread id.")] = None,
    reply_to: Annotated[str | None, typer.Option(help="Message id to reply to.")] = None,
    attachment: Annotated[
        list[str] | None,
        typer.Option(
            "--attachment",
            "-a",
            help="File path to attach. Repeat for multiple files.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(help="Send even when contention is detected."),
    ] = False,
) -> None:
    client = messaging_client(get_config())
    result = asyncio.run(
        client.send_message(
            text=text,
            channel=channel,
            thread_id=thread_id,
            reply_to=reply_to,
            attachments=attachment or [],
            force=force,
        )
    )
    echo_json(result)


@app.command("list", help="List recent messages. Defaults to DM.")
def list_command(
    channel: Annotated[str | None, typer.Option(help="Channel name or id.")] = None,
    thread_id: Annotated[str | None, typer.Option(help="Thread id.")] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum recent messages to scan."),
    ] = 25,
    query: Annotated[
        str | None,
        typer.Option("--query", "-q", help="Only include messages containing text."),
    ] = None,
    author: Annotated[
        str | None,
        typer.Option(help="Only include messages by author id or exact name."),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    echo_jsonl(
        asyncio.run(
            client.list_messages(
                channel=channel,
                thread_id=thread_id,
                limit=limit,
                query=query,
                author=author,
            )
        )
    )


@app.command("channels", help="List available messaging channels.")
def channels_command() -> None:
    client = messaging_client(get_config())
    echo_jsonl(asyncio.run(client.list_channels()))

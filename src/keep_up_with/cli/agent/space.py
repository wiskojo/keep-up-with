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
    help="Manage channels and layout.",
    no_args_is_help=True,
)
channels_app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Manage channels.",
    no_args_is_help=True,
)
sections_app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Manage channel sections.",
    no_args_is_help=True,
)


@channels_app.command("list", help="List channels.")
def list_channels_command() -> None:
    client = messaging_client(get_config())
    echo_jsonl(asyncio.run(client.list_channels()))


@channels_app.command("create", help="Create a channel.")
def create_channel_command(
    name: Annotated[str, typer.Option(help="Channel name.")],
    section: Annotated[str | None, typer.Option(help="Section name or id.")] = None,
    description: Annotated[
        str | None,
        typer.Option(help="Channel description."),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    echo_json(
        asyncio.run(
            client.create_channel(
                name=name,
                section=section,
                description=description,
            )
        )
    )


@channels_app.command("rename", help="Rename a channel.")
def rename_channel_command(
    channel: Annotated[str, typer.Option(help="Channel name or id.")],
    name: Annotated[str, typer.Option(help="New channel name.")],
) -> None:
    client = messaging_client(get_config())
    echo_json(asyncio.run(client.rename_channel(channel=channel, name=name)))


@channels_app.command("move", help="Move a channel.")
def move_channel_command(
    channel: Annotated[str, typer.Option(help="Channel name or id.")],
    section: Annotated[str | None, typer.Option(help="Section name or id.")] = None,
    before: Annotated[
        str | None,
        typer.Option(help="Place before this channel name or id."),
    ] = None,
    after: Annotated[
        str | None,
        typer.Option(help="Place after this channel name or id."),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    echo_json(
        asyncio.run(
            client.move_channel(
                channel=channel,
                section=section,
                before=before,
                after=after,
            )
        )
    )


@sections_app.command("list", help="List channel sections.")
def list_sections_command() -> None:
    client = messaging_client(get_config())
    echo_jsonl(asyncio.run(client.list_sections()))


@sections_app.command("create", help="Create a channel section.")
def create_section_command(
    name: Annotated[str, typer.Option(help="Section name.")],
) -> None:
    client = messaging_client(get_config())
    echo_json(asyncio.run(client.create_section(name=name)))


@sections_app.command("rename", help="Rename a channel section.")
def rename_section_command(
    section: Annotated[str, typer.Option(help="Section name or id.")],
    name: Annotated[str, typer.Option(help="New section name.")],
) -> None:
    client = messaging_client(get_config())
    echo_json(asyncio.run(client.rename_section(section=section, name=name)))


@sections_app.command("move", help="Move a channel section.")
def move_section_command(
    section: Annotated[str, typer.Option(help="Section name or id.")],
    before: Annotated[
        str | None,
        typer.Option(help="Place before this section name or id."),
    ] = None,
    after: Annotated[
        str | None,
        typer.Option(help="Place after this section name or id."),
    ] = None,
) -> None:
    client = messaging_client(get_config())
    echo_json(
        asyncio.run(
            client.move_section(
                section=section,
                before=before,
                after=after,
            )
        )
    )


app.add_typer(channels_app, name="channels", help="Manage channels.")
app.add_typer(sections_app, name="sections", help="Manage channel sections.")

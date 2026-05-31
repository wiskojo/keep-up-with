from __future__ import annotations

from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl, fail
from keep_up_with.core.config import get_config
from keep_up_with.core.events import EventStore

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Review and clear pending inbox items.",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("list", help="Print pending inbox items as JSONL.")
def list_command(
    unnotified: Annotated[
        bool,
        typer.Option("--unnotified", help="Only show items not yet sent into Codex."),
    ] = False,
) -> None:
    echo_jsonl(EventStore(get_config()).list_inbox(only_unnotified=unnotified))


@app.command("show", help="Show one inbox item by event id or prefix.")
def show_command(
    event_id: Annotated[str, typer.Argument(help="Event id or unique prefix.")],
) -> None:
    event = EventStore(get_config()).get_event(event_id)
    if event is None:
        fail("unknown or ambiguous event", id=event_id)
    echo_json(event)


@app.command("dismiss", help="Remove one handled item from the inbox.")
def dismiss_command(
    event_id: Annotated[str, typer.Argument(help="Event id or unique prefix.")],
) -> None:
    if not EventStore(get_config()).dismiss_inbox(event_id):
        fail("unknown inbox item", id=event_id)
    echo_json({"dismissed": True, "id": event_id})

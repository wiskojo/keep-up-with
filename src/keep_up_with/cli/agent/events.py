from __future__ import annotations

from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl, fail
from keep_up_with.core.config import get_config
from keep_up_with.core.events import EventStore

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Read the durable event history.",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("list", help="Print events as JSONL, oldest first.")
def list_command(
    limit: Annotated[
        int | None,
        typer.Option("--limit", "-n", help="Maximum events to print."),
    ] = None,
) -> None:
    echo_jsonl(EventStore(get_config()).list_events(limit=limit))


@app.command("show", help="Show one event by id or unique prefix.")
def show_command(
    event_id: Annotated[str, typer.Argument(help="Event id or unique prefix.")],
) -> None:
    event = EventStore(get_config()).get_event(event_id)
    if event is None:
        fail("unknown or ambiguous event", id=event_id)
    echo_json(event)

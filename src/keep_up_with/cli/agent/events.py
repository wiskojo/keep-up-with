from __future__ import annotations

from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl, fail
from keep_up_with.core.config import get_config
from keep_up_with.core.events import EventStore

MAX_EVENTS = 100

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="View recorded events",
    no_args_is_help=True,
)


@app.command("list", help="Print recorded events as JSONL")
def list_command(
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            help=f"Maximum events to print, hard-capped at {MAX_EVENTS}",
            min=1,
            max=MAX_EVENTS,
        ),
    ] = None,
    since: Annotated[
        str | None,
        typer.Option(help="Only include events at or after this ISO timestamp"),
    ] = None,
    until: Annotated[
        str | None,
        typer.Option(help="Only include events at or before this ISO timestamp"),
    ] = None,
    query: Annotated[
        str | None,
        typer.Option(
            "--query",
            "-q",
            help="Only include events containing this text, e.g. a URL or keyword",
        ),
    ] = None,
) -> None:
    echo_jsonl(
        EventStore(get_config()).list_events(
            limit=limit or MAX_EVENTS,
            since=since,
            until=until,
            query=query,
        )
    )


@app.command("show", help="Show one event by id or unique prefix")
def show_command(
    event_id: Annotated[str, typer.Argument(help="Event id or unique prefix")],
) -> None:
    event = EventStore(get_config()).get_event(event_id)
    if event is None:
        fail("unknown or ambiguous event", id=event_id)
    echo_json(event)

from __future__ import annotations

from typing import Annotated

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl, fail
from keep_up_with.core.config import get_config
from keep_up_with.core.events import EventStore

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Handle pending events",
    no_args_is_help=True,
)


@app.command("list", help="Print pending events as JSONL")
def list_command(
    unnotified: Annotated[
        bool,
        typer.Option("--unnotified", help="Only show items not yet sent into Codex"),
    ] = False,
    dismissed: Annotated[
        bool,
        typer.Option(
            "--dismissed",
            help="Show dismissed items with their dispositions instead of pending ones",
        ),
    ] = False,
) -> None:
    echo_jsonl(
        EventStore(get_config()).list_inbox(
            only_unnotified=unnotified,
            dismissed=dismissed,
        )
    )


@app.command("dismiss", help="Resolve pending events, recording their disposition")
def dismiss_command(
    event_ids: Annotated[
        list[str],
        typer.Argument(help="Event ids or unique prefixes; batch ids that share one disposition"),
    ],
    reason: Annotated[
        str,
        typer.Option(
            "--reason",
            help="Disposition: the published message/thread link, the prior coverage, or why it was skipped",
        ),
    ],
) -> None:
    store = EventStore(get_config())
    unknown = []
    for event_id in event_ids:
        if store.dismiss_inbox(event_id, reason=reason):
            echo_json({"dismissed": True, "id": event_id, "reason": reason})
        else:
            unknown.append(event_id)
    if unknown:
        fail("unknown inbox items", ids=unknown)

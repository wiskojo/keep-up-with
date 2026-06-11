from __future__ import annotations

import typer

from keep_up_with.cli.agent import events, inbox, message, space, subscriptions, thread, tools

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Agent-side commands for keep-up-with",
    no_args_is_help=True,
)


app.add_typer(events.app, name="events")
app.add_typer(inbox.app, name="inbox")
app.add_typer(message.app, name="message")
app.add_typer(space.app, name="space")
app.add_typer(thread.app, name="thread")
app.add_typer(tools.app, name="tools")
app.add_typer(subscriptions.app, name="subs")

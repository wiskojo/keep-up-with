from __future__ import annotations

import typer

from keep_up_with.cli.agent import events, inbox, message, space, subscriptions, thread, tools

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Agent control plane for Keep Up With.",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


app.add_typer(events.app, name="events", help="View events received by Keep Up With.")
app.add_typer(inbox.app, name="inbox", help="Review and dismiss inbox items.")
app.add_typer(message.app, name="message", help="Send and read messages.")
app.add_typer(space.app, name="space", help="Manage channels and layout.")
app.add_typer(thread.app, name="thread", help="Create and manage message threads.")
app.add_typer(tools.app, name="tools", help="Use configured tools.")
app.add_typer(subscriptions.app, name="subs", help="Show configured subscriptions.")

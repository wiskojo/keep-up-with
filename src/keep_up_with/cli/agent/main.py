from __future__ import annotations

import typer
from typer.main import get_command

from keep_up_with.cli.agent import events, inbox, message, space, subscriptions, thread

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Agent control plane for Keep Up With.",
    no_args_is_help=True,
)


app.add_typer(events.app, name="events", help="View events received by Keep Up With.")
app.add_typer(inbox.app, name="inbox", help="Review and dismiss inbox items.")
app.add_typer(message.app, name="message", help="Send and read messages.")
app.add_typer(space.app, name="space", help="Manage channels and layout.")
app.add_typer(thread.app, name="thread", help="Create and manage message threads.")
app.add_typer(subscriptions.app, name="subs", help="Show configured subscriptions.")


@app.command(
    "tools",
    add_help_option=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Use configured tools.",
)
def tools_command(ctx: typer.Context) -> None:
    from keep_up_with.cli.agent.tools import build_tools_app

    get_command(build_tools_app()).main(
        args=list(ctx.args),
        prog_name="cli tools",
        standalone_mode=True,
    )

from __future__ import annotations

import typer
from typer.main import get_command

from keep_up_with.cli.agent import events, inbox, message, space, subscriptions, thread

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Agent control plane for keep-up-with.",
    no_args_is_help=True,
)


app.add_typer(events.app, name="events")
app.add_typer(inbox.app, name="inbox")
app.add_typer(message.app, name="message")
app.add_typer(space.app, name="space")
app.add_typer(thread.app, name="thread")
app.add_typer(subscriptions.app, name="subs")


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

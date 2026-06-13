from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

import typer

from keep_up_with.cli.agent.output import echo_json, echo_jsonl
from keep_up_with.core.config import get_config
from keep_up_with.integrations.base import DataIntegration, Tool, ToolContext
from keep_up_with.integrations.registry import data_integrations, missing_env


def tool_command(integration: DataIntegration, tool: Tool) -> Callable[..., None]:
    def command(*args: Any, **kwargs: Any) -> None:
        config = get_config()
        if not config.integration_enabled(integration.name):
            typer.echo(
                f"{integration.name} is not enabled. Tell the user to enable it with `kuw setup`.",
                err=True,
            )
            raise typer.Exit(1)
        missing = missing_env(config, integration)
        if missing:
            typer.echo(
                f"{integration.name} missing environment values: {', '.join(missing)}",
                err=True,
            )
            raise typer.Exit(1)
        context = ToolContext(
            config=config,
            integration=integration.name,
            settings=config.integration(integration.name),
        )
        try:
            result = tool.function(context, *args, **kwargs)
        except Exception as error:
            typer.echo(f"{type(error).__name__}: {error}", err=True)
            raise typer.Exit(1) from error
        if isinstance(result, (list, tuple)):
            echo_jsonl(result)
        else:
            echo_json(result)

    command.__name__ = tool.function.__name__
    command.__doc__ = tool.function.__doc__
    command.__signature__ = resolved_signature(tool.function, skip_context=True)  # type: ignore[attr-defined]
    return command


def resolved_signature(
    function: Callable[..., Any],
    *,
    skip_context: bool = False,
) -> inspect.Signature:
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    parameters = [
        parameter.replace(annotation=hints.get(name, parameter.annotation))
        for name, parameter in signature.parameters.items()
    ]
    if skip_context:
        parameters = parameters[1:]
    return signature.replace(
        parameters=parameters,
        return_annotation=hints.get("return", signature.return_annotation),
    )


def build_tools_app() -> typer.Typer:
    app = typer.Typer(
        add_completion=False,
        invoke_without_command=True,
        help="Run tools to access and work with different kinds of data",
        no_args_is_help=False,
    )
    try:
        configured_integrations = data_integrations(get_config())
    except RuntimeError:
        configured_integrations = []

    @app.callback(invoke_without_command=True)
    def main(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            if not configured_integrations:
                typer.echo("No tools enabled. Enable integrations with `kuw setup`.")
                raise typer.Exit()
            typer.echo(ctx.get_help())
            raise typer.Exit()

    for integration in configured_integrations:
        if integration.tools:
            help_text = integration.description or f"Use {integration.name} tools."
            integration_app = typer.Typer(
                add_completion=False,
                invoke_without_command=True,
                help=help_text,
                no_args_is_help=True,
            )

            for tool in integration.tools:
                integration_app.command(tool.name, help=tool.help)(
                    tool_command(integration, tool)
                )
            app.add_typer(
                integration_app,
                name=integration.name,
            )
    return app


app = build_tools_app()

from __future__ import annotations

from typing import Any

import typer

from keep_up_with.cli.agent.output import echo_jsonl
from keep_up_with.core.config import get_config
from keep_up_with.integrations.base import DataIntegration, Subscription
from keep_up_with.integrations.registry import (
    available_data_integrations,
    missing_env,
)

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Show enabled data subscriptions.",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("list", help="Print enabled data subscriptions as JSONL.")
def list_command() -> None:
    echo_jsonl(subscription_rows())


def subscription_rows() -> list[dict[str, Any]]:
    config = get_config()
    rows: list[dict[str, Any]] = []
    for integration in sorted(available_data_integrations(), key=lambda item: item.name):
        settings = config.integration(integration.name)
        enabled = config.integration_enabled(integration.name)
        if not enabled:
            continue
        missing = list(missing_env(config, integration))
        rows.extend(
            subscription_row(
                connector=integration.name,
                kind="data",
                enabled=enabled,
                settings=settings,
                missing=missing,
                subscription=subscription,
                watches=watches(integration, settings),
            )
            for subscription in integration.subscriptions
        )
    return rows


def subscription_row(
    *,
    connector: str,
    kind: str,
    enabled: bool,
    settings: dict[str, Any],
    missing: list[str],
    subscription: Subscription,
    watches: dict[str, Any],
) -> dict[str, Any]:
    return {
        "connector": connector,
        "kind": kind,
        "subscription": subscription.name,
        "enabled": enabled,
        "runnable": enabled and not missing,
        "interval_seconds": interval_seconds(subscription, settings),
        "missing_env": missing,
        "watches": watches,
    }


def interval_seconds(
    subscription: Subscription,
    settings: dict[str, Any],
) -> float | None:
    if subscription.default_interval_seconds is None:
        return None
    return float(settings.get("interval_seconds") or subscription.default_interval_seconds)


def watches(integration: DataIntegration, settings: dict[str, Any]) -> dict[str, Any]:
    return {
        parameter.name: settings.get(parameter.name) or []
        for parameter in integration.parameters
    }

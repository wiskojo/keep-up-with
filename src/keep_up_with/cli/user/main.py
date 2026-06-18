from __future__ import annotations

import typer

from keep_up_with.cli.user import ui
from keep_up_with.cli.user.reset import reset_runtime
from keep_up_with.cli.user.setup import run_setup
from keep_up_with.cli.user.start import start_services, stop_services
from keep_up_with.cli.user.status import run_status
from keep_up_with.core.config import get_config, get_paths

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Manage keep-up-with on this machine",
    no_args_is_help=True,
)


@app.command(help="Run setup wizard")
def setup() -> None:
    paths = get_paths()
    try:
        run_setup(paths)
    except KeyboardInterrupt as error:
        ui.error("Setup cancelled.")
        raise typer.Exit(130) from error
    except (FileNotFoundError, RuntimeError) as error:
        ui.error(f"Error: {error}")
        raise typer.Exit(1) from error
    ui.summary(
        [
            ("home", str(paths.home)),
            ("workspace", str(paths.workspace)),
            ("config", str(paths.config)),
            ("env", str(paths.env)),
        ]
    )


@app.command(help="Start the runtime")
def start() -> None:
    try:
        results = start_services(get_config())
    except RuntimeError as error:
        ui.error(f"Error: {error}")
        raise typer.Exit(1) from error
    print_results(results)


@app.command(help="Stop the runtime")
def stop() -> None:
    print_results(stop_services(get_config()))


@app.command(help="Reset runtime state")
def reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    try:
        config = get_config()
        did_reset = reset_runtime(config, yes=yes)
    except RuntimeError as error:
        ui.error(f"Error: {error}")
        raise typer.Exit(1) from error
    if not did_reset:
        return
    ui.success("Runtime state reset.")
    ui.info("config and env were preserved.")
    ui.info("workspace was recreated.")
    ui.info("next `kup start` will create a new Codex thread.")


@app.command(help="Show runtime status")
def status() -> None:
    try:
        run_status(get_config())
    except RuntimeError as error:
        ui.error(f"Error: {error}")
        raise typer.Exit(1) from error


def print_results(results) -> None:
    for result in results:
        pid = f" pid={result.pid}" if result.pid is not None else ""
        log = f" log={result.log}" if result.log else ""
        ui.info(f"{result.name}: {result.action}{pid}{log}")

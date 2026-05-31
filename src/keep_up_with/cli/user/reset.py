from __future__ import annotations

import shutil
from pathlib import Path

from keep_up_with.cli.user import ui
from keep_up_with.cli.user.setup import write_default_workspace
from keep_up_with.cli.user.start import stop_services
from keep_up_with.core.config import KeepUpWithConfig


def reset_runtime(config: KeepUpWithConfig, *, yes: bool = False) -> bool:
    if not yes and not ui.confirm(
        "Reset runtime state and workspace? This keeps config and secrets.",
        default=False,
    ):
        ui.warning("Cancelled.")
        return False

    stop_services(config)
    reset_events(config.paths.events_db)
    shutil.rmtree(config.paths.run, ignore_errors=True)
    shutil.rmtree(config.paths.logs, ignore_errors=True)
    shutil.rmtree(config.paths.workspace, ignore_errors=True)
    config.paths.run.mkdir(parents=True, exist_ok=True)
    config.paths.logs.mkdir(parents=True, exist_ok=True)
    config.paths.workspace.mkdir(parents=True, exist_ok=True)
    write_default_workspace(config.paths)
    return True


def reset_events(path: Path) -> None:
    for candidate in (
        path,
        path.with_name(f"{path.name}-wal"),
        path.with_name(f"{path.name}-shm"),
    ):
        candidate.unlink(missing_ok=True)

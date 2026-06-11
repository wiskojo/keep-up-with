from __future__ import annotations

import json
import sqlite3

from keep_up_with.cli.user import ui
from keep_up_with.cli.user.codex_daemon import probe_codex_daemon
from keep_up_with.cli.user.start import Service, is_running, pid_path, services
from keep_up_with.core.config import KeepUpWithConfig
from keep_up_with.integrations.registry import (
    available_data_integrations,
    configured_messaging_integration,
    missing_env,
)


def run_status(config: KeepUpWithConfig) -> None:
    ui.header("Runtime")
    ui.info(f"codex daemon: {codex_daemon_status()}")
    for service in services(config):
        pid = read_running_pid(config, service)
        state = f"running pid={pid}" if pid is not None else "stopped"
        ui.info(f"{service.name}: {state}")
    ui.info(f"thread: {thread_status(config)}")
    ui.info(f"events: {event_status(config)}")

    ui.header("Messaging")
    messaging = configured_messaging_integration(config)
    missing = missing_env(config, messaging)
    state = "configured" if not missing else "missing " + ", ".join(missing)
    ui.info(f"{messaging.name}: {state}")

    ui.header("Integrations")
    for integration in sorted(available_data_integrations(), key=lambda item: item.name):
        enabled = config.integration_enabled(integration.name)
        missing = missing_env(config, integration) if enabled else ()
        state = "on" if enabled else "off"
        if missing:
            state += "; missing " + ", ".join(missing)
        details = connector_details(config, integration)
        suffix = f"; {details}" if details else ""
        ui.info(f"{integration.name}: {state}{suffix}")


def read_running_pid(config: KeepUpWithConfig, service: Service) -> int | None:
    try:
        pid = int(pid_path(config, service).read_text().strip())
    except (FileNotFoundError, ValueError):
        return None
    return pid if is_running(pid) else None


def connector_details(config: KeepUpWithConfig, integration) -> str:
    section = config.integration(integration.name)
    parts: list[str] = []
    for parameter in integration.parameters:
        values = section.get(parameter.name) or []
        if isinstance(values, list):
            parts.append(f"{len(values)} {parameter.name}")
    return ", ".join(parts)


def codex_daemon_status() -> str:
    probe = probe_codex_daemon()
    if not probe.running:
        return f"unreachable ({probe.detail})" if probe.detail else "unreachable"
    return f"running {probe.version}".strip()


def thread_status(config: KeepUpWithConfig) -> str:
    try:
        data = json.loads(config.paths.thread.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return "not created"
    thread_id = str(data.get("thread_id") or "")
    return thread_id or "not created"


def event_status(config: KeepUpWithConfig) -> str:
    if not config.paths.events_db.exists():
        return "0 events, 0 inbox"
    with sqlite3.connect(config.paths.events_db) as db:
        events = db.execute("select count(*) from events").fetchone()[0]
        inbox = db.execute("select count(*) from inbox").fetchone()[0]
    return f"{events} events, {inbox} inbox"

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from keep_up_with.cli.user.codex_daemon import probe_codex_daemon
from keep_up_with.cli.user.setup import (
    keep_up_with_presets,
    space_plan,
    write_default_workspace,
)
from keep_up_with.core.config import (
    AppSettings,
    KeepUpWithPaths,
    KeepUpWithSettings,
    MessagingSettings,
    load_config,
    write_config,
)
from keep_up_with.core.events import EventStore
from keep_up_with.integrations.registry import available_data_integrations, messaging_client
from keep_up_with.runtime.codex import JsonRpcClient
from keep_up_with.runtime.gateway import initialize


ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_SETTLE_SECONDS = 3
MAX_SETTLE_SECONDS = 5


@dataclass(frozen=True)
class RunContext:
    case_dir: Path
    run_dir: Path
    paths: KeepUpWithPaths
    output: Path
    timeout_seconds: int
    settle_seconds: int


def main() -> None:
    parser = argparse.ArgumentParser(description="Run keep-up-with eval cases.")
    parser.add_argument("case", help="Case name under evals/cases")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=RUNS,
        help="Directory for run outputs",
    )
    args = parser.parse_args()

    case_dir = ROOT / "cases" / args.case
    if not case_dir.exists():
        raise SystemExit(f"unknown eval case: {args.case}")
    require_codex_daemon()

    context = create_run(case_dir, args.runs_dir)
    print(f"run: {context.run_dir}", flush=True)
    process = start_gateway(context)
    try:
        wait_for_thread(context, process, timeout_seconds=60)
        wait_until_caught_up(context, process, timeout_seconds=context.timeout_seconds)
        run_batches(context, process)
    finally:
        stop_process(process)
    print(f"output: {context.output}", flush=True)


def require_codex_daemon() -> None:
    probe = probe_codex_daemon()
    if not probe.running:
        suffix = f": {probe.detail}" if probe.detail else ""
        raise SystemExit(
            "Codex app-server daemon is not running. "
            "Start it with `codex app-server daemon start` and retry"
            f"{suffix}"
        )


def create_run(case_dir: Path, runs_dir: Path) -> RunContext:
    case = load_case(case_dir)
    run_name = f"{case['name']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = runs_dir / run_name
    home = run_dir / "home"
    output = run_dir / "output"
    paths = KeepUpWithPaths(
        home=home,
        config=home / "config.toml",
        env=home / ".env",
        workspace=home / "workspace",
        logs=home / "logs",
        run=home / "run",
        events_db=home / "events.sqlite",
        thread=home / "run" / "thread.json",
    )
    for path in (paths.home, paths.workspace, paths.logs, paths.run, output):
        path.mkdir(parents=True, exist_ok=True)
    copy_case(case_dir, run_dir / "case")
    copy_env(paths.env)
    write_eval_config(paths, output)
    write_default_workspace(paths)
    apply_preset_space(paths, str(case.get("workspace", {}).get("preset") or "ai"))
    return RunContext(
        case_dir=case_dir,
        run_dir=run_dir,
        paths=paths,
        output=output,
        timeout_seconds=int(case.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS),
        settle_seconds=min(
            MAX_SETTLE_SECONDS,
            int(case.get("settle_seconds") or DEFAULT_SETTLE_SECONDS),
        ),
    )


def load_case(case_dir: Path) -> dict[str, Any]:
    path = case_dir / "case.toml"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    with path.open("rb") as file:
        data = tomllib.load(file)
    data.setdefault("name", case_dir.name)
    return data


def copy_case(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in ("case.toml", "events.json", "expected.md"):
        src = source / name
        if src.exists():
            shutil.copy2(src, target / name)


def copy_env(target: Path) -> None:
    source = Path("~/.keep-up-with/.env").expanduser()
    if source.exists():
        shutil.copy2(source, target)
    else:
        target.touch(mode=0o600, exist_ok=True)


def write_eval_config(paths: KeepUpWithPaths, output: Path) -> None:
    integrations = {
        integration.name: integration.default_config(enabled=True)
        for integration in available_data_integrations()
    }
    settings = KeepUpWithSettings(
        app=AppSettings(eval_mode=True),
        messaging=MessagingSettings(
            integration="file",
            output_dir=str(output),
            user_id="eval-user",
            mention="eval-user",
        ),
        integrations=integrations,
    )
    write_config(paths, settings)


def apply_preset_space(paths: KeepUpWithPaths, preset_name: str) -> None:
    presets = keep_up_with_presets()
    preset = presets.get(preset_name)
    if preset is None:
        return
    config = load_config(paths)
    client = messaging_client(config)
    asyncio.run(client.apply_space(space_plan([preset]), reset=True))


def start_gateway(context: RunContext) -> subprocess.Popen:
    env = os.environ.copy()
    env["KEEP_UP_WITH_HOME"] = str(context.paths.home)
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env.get('PATH', '')}"
    log_path = context.paths.logs / "gateway.log"
    output = log_path.open("a")
    return subprocess.Popen(
        (sys.executable, "-m", "keep_up_with.runtime.gateway"),
        cwd=context.paths.workspace,
        env=env,
        stdout=output,
        stderr=output,
        start_new_session=True,
    )


def wait_for_thread(
    context: RunContext,
    process: subprocess.Popen,
    *,
    timeout_seconds: int,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        ensure_running(process, context)
        thread_id = read_thread_id(context)
        if thread_id:
            return thread_id
        time.sleep(0.5)
    raise RuntimeError(f"gateway did not create a thread; see {context.paths.logs / 'gateway.log'}")


def read_thread_id(context: RunContext) -> str | None:
    try:
        data = json.loads(context.paths.thread.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    value = data.get("thread_id")
    return str(value) if value else None


def run_batches(context: RunContext, process: subprocess.Popen) -> None:
    batches = json.loads((context.case_dir / "events.json").read_text())
    if not isinstance(batches, list):
        raise RuntimeError("events.json must contain a list of batches")
    for index, batch in enumerate(batches, start=1):
        name = str(batch.get("name") or f"batch {index}")
        events = batch.get("events")
        if not isinstance(events, list):
            raise RuntimeError(f"{name}: events must be a list")
        print(f"injecting {name}: {len(events)} event(s)", flush=True)
        previous_turn_count = turn_count(context, process)
        event_ids = inject_events(context, events)
        wait_for_notified(context, event_ids, timeout_seconds=60)
        wait_until_idle(
            context,
            process,
            min_turn_count=previous_turn_count + 1,
            timeout_seconds=int(batch.get("timeout_seconds") or context.timeout_seconds),
        )
        wait_for_output_settle(context, seconds=min(
            MAX_SETTLE_SECONDS,
            int(batch.get("settle_seconds") or context.settle_seconds),
        ))


def wait_until_caught_up(
    context: RunContext,
    process: subprocess.Popen,
    *,
    timeout_seconds: int,
) -> None:
    print("gateway: waiting to catch up", flush=True)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        ensure_running(process, context)
        if unnotified_inbox_count(context) == 0:
            wait_until_idle(
                context,
                process,
                timeout_seconds=max(1, int(deadline - time.monotonic())),
            )
            if unnotified_inbox_count(context) == 0:
                wait_for_output_settle(context, seconds=context.settle_seconds)
                return
        time.sleep(0.5)
    raise RuntimeError(f"gateway did not catch up within {timeout_seconds}s")


def unnotified_inbox_count(context: RunContext) -> int:
    try:
        with sqlite3.connect(context.paths.events_db) as db:
            row = db.execute(
                "select count(*) from inbox where notified_at is null"
            ).fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row[0]) if row else 0


def inject_events(context: RunContext, rows: list[dict[str, Any]]) -> list[str]:
    store = EventStore(load_config(context.paths))
    event_ids: list[str] = []
    for row in rows:
        event = store.record(
            integration=str(row["integration"]),
            kind=str(row["kind"]),
            external_id=str(row["external_id"]),
            summary=str(row["summary"]),
            refs=row.get("refs") if isinstance(row.get("refs"), dict) else {},
            data=row.get("data") if isinstance(row.get("data"), dict) else {},
            high_priority=bool(row.get("high_priority", False)),
        )
        if event is not None:
            event_ids.append(event.id)
    return event_ids


def wait_for_notified(
    context: RunContext,
    event_ids: list[str],
    *,
    timeout_seconds: int,
) -> None:
    if not event_ids:
        return
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with sqlite3.connect(context.paths.events_db) as db:
            rows = db.execute(
                f"""
                select count(*)
                from inbox
                where event_id in ({','.join('?' for _ in event_ids)})
                  and notified_at is not null
                """,
                event_ids,
            ).fetchone()
        if rows and int(rows[0]) == len(event_ids):
            return
        time.sleep(0.5)
    raise RuntimeError("gateway did not notify Codex for injected batch")


def wait_until_idle(
    context: RunContext,
    process: subprocess.Popen,
    *,
    timeout_seconds: int,
    min_turn_count: int = 0,
) -> None:
    thread_id = wait_for_thread(context, process, timeout_seconds=60)
    client = JsonRpcClient()
    client.connect()
    try:
        initialize(client)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            ensure_running(process, context)
            result = client.request(
                "thread/read",
                {"threadId": thread_id, "includeTurns": True},
            )
            thread = result.get("thread", {})
            if count_turns(thread) >= min_turn_count and thread_idle(thread):
                return
            time.sleep(1)
    finally:
        client.close()
    raise RuntimeError(f"thread did not become idle within {timeout_seconds}s")


def thread_idle(thread: dict[str, Any]) -> bool:
    status = thread.get("status")
    if isinstance(status, dict) and status.get("type") == "active":
        return False
    turns = thread.get("turns") if isinstance(thread.get("turns"), list) else []
    if turns:
        latest = turns[-1]
        if isinstance(latest, dict) and latest.get("status") == "inProgress":
            return False
    return True


def turn_count(context: RunContext, process: subprocess.Popen) -> int:
    thread_id = wait_for_thread(context, process, timeout_seconds=60)
    client = JsonRpcClient()
    client.connect()
    try:
        initialize(client)
        result = client.request(
            "thread/read",
            {"threadId": thread_id, "includeTurns": True},
        )
        return count_turns(result.get("thread", {}))
    finally:
        client.close()


def count_turns(thread: dict[str, Any]) -> int:
    turns = thread.get("turns")
    return len(turns) if isinstance(turns, list) else 0


def wait_for_output_settle(context: RunContext, *, seconds: int) -> None:
    if seconds <= 0:
        return
    stable_since = time.monotonic()
    fingerprint = output_fingerprint(context.output)
    while time.monotonic() - stable_since < seconds:
        time.sleep(0.5)
        current = output_fingerprint(context.output)
        if current != fingerprint:
            fingerprint = current
            stable_since = time.monotonic()


def output_fingerprint(path: Path) -> tuple[tuple[str, int, int], ...]:
    if not path.exists():
        return ()
    rows = []
    for item in sorted(path.rglob("*")):
        if item.is_file():
            stat = item.stat()
            rows.append((item.relative_to(path).as_posix(), stat.st_size, stat.st_mtime_ns))
    return tuple(rows)


def ensure_running(process: subprocess.Popen, context: RunContext) -> None:
    if process.poll() is not None:
        raise RuntimeError(
            f"gateway exited with {process.returncode}; see {context.paths.logs / 'gateway.log'}"
        )


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(50):
        if process.poll() is not None:
            return
        time.sleep(0.1)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


if __name__ == "__main__":
    main()

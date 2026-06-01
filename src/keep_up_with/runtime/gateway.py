from __future__ import annotations

import json
import socket
import sys
import time
import traceback
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Event as ThreadEvent, Thread
from textwrap import dedent
from typing import Any

from keep_up_with.core.config import KeepUpWithConfig, KeepUpWithPaths, get_config, load_config
from keep_up_with.core.events import EventStore, InboxItem
from keep_up_with.integrations.base import Subscription, SubscriptionContext
from keep_up_with.integrations.registry import data_integrations, messaging_integration
from keep_up_with.runtime.codex import JsonRpcClient

ERROR_EVENT_SECONDS = 6 * 60 * 60
CONFIG_CHECK_SECONDS = 3.0
HIGH_WAKE_DELAY_SECONDS = 5.0
LOW_WAKE_DELAY_SECONDS = 30.0
MAX_SUMMARY = 180


@dataclass(frozen=True)
class SubscriptionKey:
    integration: str
    subscription: str


@dataclass
class RunningSubscription:
    key: SubscriptionKey
    signature: str
    thread: Thread
    stop_event: ThreadEvent


@dataclass
class CodexState:
    thread_id: str | None = None
    active_turn_id: str | None = None
    high_queued_at: float | None = None
    low_queued_at: float | None = None


def main() -> None:
    try:
        run_gateway(get_config())
    except Exception as error:
        print(f"gateway failed: {error}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1) from error


def run_gateway(config: KeepUpWithConfig) -> None:
    store = EventStore(config)
    running: dict[SubscriptionKey, RunningSubscription] = {}
    fingerprint = config_fingerprint(config.paths)
    state = read_thread_state(config.paths.thread)
    client = JsonRpcClient(config.settings.app.codex_socket)
    client.connect()
    try:
        initialize(client)
        state.thread_id, created = ensure_thread(config, client, state.thread_id)
        write_thread_state(config.paths.thread, state, config.settings.app.thread_name)
        if created:
            start_turn(client, state, initial_turn_message(config))

        start_messaging(config, store)
        reconcile_data(config, store, running)
        while True:
            drain(client, state)
            wake_on_inbox(
                client,
                state,
                store,
                now=time.monotonic(),
                high_delay_seconds=HIGH_WAKE_DELAY_SECONDS,
                low_delay_seconds=LOW_WAKE_DELAY_SECONDS,
            )
            write_thread_state(config.paths.thread, state, config.settings.app.thread_name)
            time.sleep(CONFIG_CHECK_SECONDS)
            current_fingerprint = config_fingerprint(config.paths)
            if current_fingerprint != fingerprint:
                try:
                    config = load_config(config.paths)
                except RuntimeError:
                    traceback.print_exc(file=sys.stderr)
                    continue
                fingerprint = current_fingerprint
            reconcile_data(config, store, running)
    finally:
        client.close()
        stop_all(running)


def initialize(client: JsonRpcClient) -> None:
    client.request(
        "initialize",
        {
            "clientInfo": {
                "name": "keep-up-with",
                "title": "keep-up-with",
                "version": "0.1.0",
            },
            "capabilities": {"experimentalApi": True},
        },
    )


def ensure_thread(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
    thread_id: str | None,
) -> tuple[str, bool]:
    params = thread_params(config)
    if thread_id:
        try:
            result = client.request("thread/resume", {"threadId": thread_id, **params})
            return str(result["thread"]["id"]), False
        except RuntimeError as error:
            print(
                f"gateway could not resume thread {thread_id}: {error}",
                file=sys.stderr,
                flush=True,
            )
    result = client.request("thread/start", params)
    return str(result["thread"]["id"]), True


def thread_params(config: KeepUpWithConfig) -> dict[str, Any]:
    return {
        "cwd": str(config.paths.workspace),
        "approvalPolicy": "on-request",
        "approvalsReviewer": "auto_review",
        "sandbox": "workspace-write",
        "config": {
            "sandbox_workspace_write": {
                "network_access": True,
                "exclude_tmpdir_env_var": False,
                "exclude_slash_tmp": False,
            },
        },
        "sessionStartSource": "startup",
        "threadSource": "user",
    }


def initial_turn_message(config: KeepUpWithConfig) -> str:
    return dedent(
        f"""
        $keep-up-with

        You were just started.

        Follow the startup/onboarding flow in the keep-up-with skill.
        """
    ).strip()


def start_messaging(config: KeepUpWithConfig, store: EventStore) -> None:
    messaging = messaging_integration(config)
    for subscription in messaging.subscriptions:
        start_subscription(
            config=config,
            store=store,
            integration=messaging.name,
            settings=config.messaging().model_dump(),
            subscription=subscription,
            daemon=True,
            baseline_first_poll=False,
        )


def reconcile_data(
    config: KeepUpWithConfig,
    store: EventStore,
    running: dict[SubscriptionKey, RunningSubscription],
) -> None:
    desired: dict[SubscriptionKey, tuple[str, Subscription, dict[str, Any]]] = {}
    signatures: dict[SubscriptionKey, str] = {}
    for integration in data_integrations(config):
        settings = config.integration(integration.name)
        signature = subscription_signature(config, integration.name, settings)
        for subscription in integration.subscriptions:
            key = SubscriptionKey(integration.name, subscription.name)
            desired[key] = (integration.name, subscription, settings)
            signatures[key] = signature

    for key, active in list(running.items()):
        stale = (
            key not in desired
            or active.signature != signatures[key]
            or not active.thread.is_alive()
        )
        if stale:
            active.stop_event.set()
            active.thread.join(timeout=1)
            del running[key]

    for key, (integration, subscription, settings) in desired.items():
        if key in running:
            continue
        stop_event = ThreadEvent()
        thread = start_subscription(
            config=config,
            store=store,
            integration=integration,
            settings=settings,
            subscription=subscription,
            stop_event=stop_event,
            baseline_first_poll=subscription.default_interval_seconds is not None,
        )
        running[key] = RunningSubscription(
            key=key,
            signature=signatures[key],
            thread=thread,
            stop_event=stop_event,
        )


def start_subscription(
    *,
    config: KeepUpWithConfig,
    store: EventStore,
    integration: str,
    settings: dict[str, Any],
    subscription: Subscription,
    stop_event: ThreadEvent | None = None,
    daemon: bool = False,
    baseline_first_poll: bool = False,
) -> Thread:
    thread = Thread(
        target=run_subscription,
        args=(
            config,
            store,
            integration,
            settings,
            subscription,
            stop_event,
            baseline_first_poll,
        ),
        daemon=daemon,
    )
    thread.start()
    return thread


def run_subscription(
    config: KeepUpWithConfig,
    store: EventStore,
    integration: str,
    settings: dict[str, Any],
    subscription: Subscription,
    stop_event: ThreadEvent | None = None,
    baseline_first_poll: bool = False,
) -> None:
    consecutive_failures = 0
    last_error_at: dict[str, float] = {}
    first_run = True
    effective_stop_event = stop_event or ThreadEvent()
    while not effective_stop_event.is_set():
        context = SubscriptionContext(
            config=config,
            record_event=partial(
                store.record,
                pending=not (baseline_first_poll and first_run),
            ),
            integration=integration,
            settings=settings,
            stop_event=effective_stop_event,
        )
        try:
            subscription.run(context)
            consecutive_failures = 0
            first_run = False
        except Exception as error:
            consecutive_failures += 1
            traceback.print_exception(error, file=sys.stderr)
            emit_error(
                store,
                context,
                subscription.name,
                error,
                consecutive_failures,
                last_error_at,
            )
            context.wait(5)
            continue
        sleep_seconds = 5.0
        if subscription.default_interval_seconds is not None:
            sleep_seconds = float(
                context.settings().get("interval_seconds")
                or subscription.default_interval_seconds
            )
        context.wait(sleep_seconds)


def drain(client: JsonRpcClient, state: CodexState) -> None:
    while True:
        try:
            message = client.recv(timeout=0.01)
        except socket.timeout:
            return
        method = message.get("method")
        params = (
            message.get("params") if isinstance(message.get("params"), dict) else {}
        )
        if method == "turn/completed":
            turn = params.get("turn", {})
            if turn.get("id") == state.active_turn_id:
                state.active_turn_id = None
        elif method == "thread/status/changed":
            status = params.get("status", {})
            if isinstance(status, dict) and status.get("type") == "idle":
                state.active_turn_id = None
        elif method == "error":
            print(f"gateway app-server error: {params}", file=sys.stderr, flush=True)


def wake_on_inbox(
    client: JsonRpcClient,
    state: CodexState,
    store: EventStore,
    *,
    now: float,
    high_delay_seconds: float,
    low_delay_seconds: float,
) -> None:
    items = store.list_inbox(only_unnotified=True)
    if not items:
        state.high_queued_at = None
        state.low_queued_at = None
        return

    high_items = [item for item in items if item.event.high_priority]
    low_items = [item for item in items if not item.event.high_priority]
    if high_items and state.high_queued_at is None:
        state.high_queued_at = now
    if low_items and state.low_queued_at is None:
        state.low_queued_at = now

    if high_items and due(state.high_queued_at, now, high_delay_seconds):
        send_wake(client, state, store, high_items)
        state.high_queued_at = None
        return

    if low_items and due(state.low_queued_at, now, low_delay_seconds):
        send_wake(client, state, store, low_items)
        state.low_queued_at = None


def send_wake(
    client: JsonRpcClient,
    state: CodexState,
    store: EventStore,
    items: list[InboxItem],
) -> None:
    if state.thread_id is None:
        raise RuntimeError("cannot wake without thread id")
    text = render_wake(items, len(store.list_inbox()))
    start_turn(client, state, text)
    store.mark_notified([item.event.id for item in items])


def start_turn(client: JsonRpcClient, state: CodexState, text: str) -> None:
    if state.thread_id is None:
        raise RuntimeError("cannot start turn without thread id")
    result = client.request(
        "turn/start",
        {"threadId": state.thread_id, "input": input_text(text)},
    )
    turn = result.get("turn", {})
    if turn.get("status") == "inProgress":
        state.active_turn_id = str(turn["id"])


def render_wake(items: list[InboxItem], inbox_count: int) -> str:
    noun = "notification" if len(items) == 1 else "notifications"
    lines = [f"{len(items)} new {noun} received ({inbox_count} in inbox):", ""]
    for index, item in enumerate(items, start=1):
        event = item.event
        lines.append(
            f"{index}. [{event.integration}.{event.kind} {event.id[:6]}] "
            f"{truncate(event.summary)}"
        )
        refs = " ".join(f"{key}={value}" for key, value in event.refs.items())
        if refs:
            lines.append(f"   ref: {refs}")
    return "\n".join(lines)


def input_text(text: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": text, "text_elements": []}]


def due(queued_at: float | None, now: float, delay: float) -> bool:
    return queued_at is not None and now - queued_at >= delay


def read_thread_state(path: Path) -> CodexState:
    try:
        data = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return CodexState()
    return CodexState(thread_id=data.get("thread_id"))


def write_thread_state(path: Path, state: CodexState, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "thread_id": state.thread_id,
                "name": name,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def stop_all(running: dict[SubscriptionKey, RunningSubscription]) -> None:
    for active in running.values():
        active.stop_event.set()
    for active in running.values():
        active.thread.join(timeout=1)


def subscription_signature(
    config: KeepUpWithConfig,
    integration: str,
    settings: dict[str, Any],
) -> str:
    return json.dumps(
        {
            "settings": settings,
            "env": config.env_values,
            "integration": integration,
        },
        sort_keys=True,
        default=str,
    )


def config_fingerprint(paths: KeepUpWithPaths) -> tuple[tuple[int, int], tuple[int, int]]:
    return file_fingerprint(paths.config), file_fingerprint(paths.env)


def file_fingerprint(path: Path) -> tuple[int, int]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return (-1, -1)
    return (stat.st_mtime_ns, stat.st_size)


def emit_error(
    store: EventStore,
    context: SubscriptionContext,
    subscription: str,
    error: Exception,
    consecutive_failures: int,
    last_error_at: dict[str, float],
) -> None:
    error_type = type(error).__name__
    now = time.monotonic()
    previous = last_error_at.get(error_type)
    if previous is not None and now - previous < ERROR_EVENT_SECONDS:
        return
    last_error_at[error_type] = now
    store.record(
        integration="keep_up_with",
        kind="subscription_error",
        external_id=f"{subscription}:{error_type}",
        summary=f"{subscription}: {error}",
        refs={"subscription": subscription, "integration": context.integration},
        data={
            "subscription": subscription,
            "integration": context.integration,
            "error_type": error_type,
            "error": str(error),
            "consecutive_failures": consecutive_failures,
        },
    )


def truncate(value: str, limit: int = MAX_SUMMARY) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


if __name__ == "__main__":
    main()

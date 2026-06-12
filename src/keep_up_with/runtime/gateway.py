from __future__ import annotations

import json
import socket
import sys
import time
import traceback
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from textwrap import dedent
from threading import Event as ThreadEvent
from threading import Thread
from typing import Any

from keep_up_with.core.config import (
    KeepUpWithConfig,
    KeepUpWithPaths,
    get_config,
    load_config,
)
from keep_up_with.core.events import EventStore, InboxItem
from keep_up_with.integrations.base import Subscription, SubscriptionContext
from keep_up_with.integrations.registry import data_integrations, messaging_integration
from keep_up_with.runtime.codex import JsonRpcClient

ERROR_EVENT_SECONDS = 6 * 60 * 60
CONFIG_CHECK_SECONDS = 3.0
HIGH_WAKE_DELAY_SECONDS = 5.0
LOW_WAKE_DELAY_SECONDS = 30.0
ROTATE_CONTEXT_USED_FRACTION = 0.75


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
    context_used: float = 0.0
    previous_thread_ids: list[str] = field(default_factory=list)


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
        first_message = ensure_thread(config, client, state)
        write_thread_state(config.paths.thread, state, config.settings.app.thread_name)
        if first_message:
            start_turn(client, state, first_message)

        start_messaging(config, store)
        reconcile_data(config, store, running)
        while True:
            drain(client, state)
            wake_on_inbox(
                config,
                client,
                state,
                store,
                now=time.monotonic(),
                high_delay_seconds=HIGH_WAKE_DELAY_SECONDS,
                low_delay_seconds=LOW_WAKE_DELAY_SECONDS,
            )
            write_thread_state(
                config.paths.thread, state, config.settings.app.thread_name
            )
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
    state: CodexState,
) -> str | None:
    """Resume or create the main thread; returns the first turn message, if any.

    The main thread is a chain: each rotation or recovery starts a fresh thread
    that points back at the previous one. The startup greeting is sent only
    when the workspace has no threads at all (fresh install or after reset).
    """
    params = thread_params(config)
    candidate = state.thread_id or latest_workspace_thread_id(config, client)
    if candidate:
        try:
            result = client.request("thread/resume", {"threadId": candidate, **params})
            state.thread_id = str(result["thread"]["id"])
            archive_stray_threads(config, client, state)
            return None
        except RuntimeError as error:
            print(
                f"gateway could not resume thread {candidate}: {error}",
                file=sys.stderr,
                flush=True,
            )
    result = client.request("thread/start", params)
    state.thread_id = str(result["thread"]["id"])
    if candidate:
        state.previous_thread_ids.append(candidate)
    state.context_used = 0.0
    name_thread(client, state.thread_id)
    archive_stray_threads(config, client, state)
    if candidate is None:
        return initial_turn_message(config)
    return continuation_turn_message(candidate)


def rotate_thread_if_due(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
    state: CodexState,
) -> str | None:
    """Rotate to a fresh thread before codex compacts the current one.

    Called on the wake path right before a turn starts, so the next wake lands
    on the new thread with the continuation pointer prepended. Returns the
    continuation message to prepend, or None when no rotation was needed.
    """
    # Codex auto-compacts somewhere around 80-95% of the context window; rotate to
    # a fresh thread comfortably before that so compaction never gets a chance to
    # replay stale history into the model's context.
    if state.thread_id is None or state.context_used < ROTATE_CONTEXT_USED_FRACTION:
        return None

    previous_thread_id = state.thread_id
    result = client.request("thread/start", thread_params(config))
    state.thread_id = str(result["thread"]["id"])
    state.previous_thread_ids.append(previous_thread_id)
    state.context_used = 0.0
    name_thread(client, state.thread_id)
    write_thread_state(config.paths.thread, state, config.settings.app.thread_name)
    print(
        f"gateway rotated thread {previous_thread_id} -> {state.thread_id}",
        file=sys.stderr,
        flush=True,
    )
    return continuation_turn_message(previous_thread_id)


def latest_workspace_thread_id(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
) -> str | None:
    threads = workspace_threads(config, client)
    if not threads:
        return None
    threads.sort(key=lambda thread: str(thread.get("updatedAt") or ""), reverse=True)
    thread_id = str(threads[0].get("id") or "")
    return thread_id or None


def name_thread(client: JsonRpcClient, thread_id: str) -> None:
    try:
        client.request(
            "thread/name/set",
            {"threadId": thread_id, "name": time.strftime("%Y-%m-%d %H:%M")},
        )
    except RuntimeError as error:
        print(f"gateway could not name thread: {error}", file=sys.stderr, flush=True)


def archive_stray_threads(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
    state: CodexState,
) -> None:
    keep = {state.thread_id, *state.previous_thread_ids}
    for thread in workspace_threads(config, client):
        thread_id = str(thread.get("id") or "")
        if thread_id and thread_id not in keep:
            client.request("thread/archive", {"threadId": thread_id})


def archive_workspace_threads(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
    *,
    keep_thread_id: str | None = None,
) -> None:
    for thread in workspace_threads(config, client):
        thread_id = str(thread.get("id") or "")
        if not thread_id or thread_id == keep_thread_id:
            continue
        client.request("thread/archive", {"threadId": thread_id})


def workspace_threads(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
) -> list[dict[str, Any]]:
    threads: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {
            "archived": False,
            "cwd": str(config.paths.workspace),
            "limit": 100,
            "sourceKinds": [],
        }
        if cursor:
            params["cursor"] = cursor
        result = client.request("thread/list", params)
        threads.extend(
            thread for thread in result.get("data", []) if isinstance(thread, dict)
        )
        cursor_value = result.get("nextCursor")
        cursor = str(cursor_value) if cursor_value else None
        if cursor is None:
            return threads


def thread_params(config: KeepUpWithConfig) -> dict[str, Any]:
    return {
        "cwd": str(config.paths.workspace),
        "approvalPolicy": "on-request",
        "approvalsReviewer": "auto_review",
        "sandbox": "workspace-write",
        "config": {
            "sandbox_workspace_write": {
                "network_access": True,
                "writable_roots": [str(config.paths.home)],
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
        You were just started. Your operating instructions are in `AGENTS.md`, and your durable context lives in `{config.paths.workspace}`. You are always allowed, and encouraged, to use subagents.

        1. Greet the user to let them know you're up. Say you're getting situated and will follow up shortly.
        2. Read `USER.md` and `MEMORY.md`, then run `cli --help` and confirm the command works.
        3. Inspect what the user keeps up with: `cli subs list` for subscriptions and `cli space channels list` for the channel layout. They have already gone through setup, so do not ask broad setup questions.
        4. Follow up by introducing yourself more fully, saying what you understand so far, getting a feel for what they care about, and asking any questions you have.

        If notifications arrive while you are getting situated, finish situating first."""
    ).strip()


def continuation_turn_message(previous_thread_id: str) -> str:
    return f"This thread continues your previous conversation thread `{previous_thread_id}`."


def start_messaging(config: KeepUpWithConfig, store: EventStore) -> None:
    messaging = messaging_integration(config)
    # Messaging credentials and subscriptions are fixed for the process lifetime.
    for subscription in messaging.subscriptions:
        start_subscription(
            config=config,
            store=store,
            integration=messaging.name,
            settings=config.messaging().model_dump(),
            subscription=subscription,
            daemon=True,
            baseline_first_run=False,
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
            baseline_first_run=subscription.baseline_first_run,
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
    baseline_first_run: bool = False,
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
            baseline_first_run,
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
    baseline_first_run: bool = False,
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
                pending=not (baseline_first_run and first_run),
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
        elif method == "thread/tokenUsage/updated":
            if params.get("threadId") == state.thread_id:
                state.context_used = context_used_fraction(params) or state.context_used
        elif method == "thread/compacted":
            if params.get("threadId") == state.thread_id:
                print(
                    "gateway: codex compacted the main thread before rotation",
                    file=sys.stderr,
                    flush=True,
                )
        elif method == "error":
            print(f"gateway app-server error: {params}", file=sys.stderr, flush=True)


def wake_on_inbox(
    config: KeepUpWithConfig,
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
    if state.active_turn_id is not None:
        return

    high_items = [item for item in items if item.event.high_priority]
    low_items = [item for item in items if not item.event.high_priority]
    if high_items and state.high_queued_at is None:
        state.high_queued_at = now
    if low_items and state.low_queued_at is None:
        state.low_queued_at = now

    if high_items and due(state.high_queued_at, now, high_delay_seconds):
        send_wake(config, client, state, store, high_items)
        state.high_queued_at = None
        return

    if low_items and due(state.low_queued_at, now, low_delay_seconds):
        send_wake(config, client, state, store, low_items)
        state.low_queued_at = None


def send_wake(
    config: KeepUpWithConfig,
    client: JsonRpcClient,
    state: CodexState,
    store: EventStore,
    items: list[InboxItem],
) -> None:
    if state.thread_id is None:
        raise RuntimeError("cannot wake without thread id")
    text = render_wake(items, len(store.list_inbox()))
    continuation = rotate_thread_if_due(config, client, state)
    if continuation:
        text = f"{continuation}\n\n{text}"
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
            f"{event.summary}"
        )
        refs = " ".join(f"{key}={value}" for key, value in event.refs.items())
        if refs:
            lines.append(f"   ref: {refs}")
    return "\n".join(lines)


def input_text(text: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": text, "text_elements": []}]


def due(queued_at: float | None, now: float, delay: float) -> bool:
    return queued_at is not None and now - queued_at >= delay


def context_used_fraction(params: dict[str, Any]) -> float | None:
    usage = params.get("tokenUsage")
    if not isinstance(usage, dict):
        return None
    window = usage.get("modelContextWindow")
    last = usage.get("last")
    if not window or not isinstance(last, dict):
        return None
    used = last.get("inputTokens")
    if not used:
        return None
    return float(used) / float(window)


def read_thread_state(path: Path) -> CodexState:
    try:
        data = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return CodexState()
    previous = data.get("previous_thread_ids")
    return CodexState(
        thread_id=data.get("thread_id"),
        previous_thread_ids=[str(item) for item in previous]
        if isinstance(previous, list)
        else [],
    )


def write_thread_state(path: Path, state: CodexState, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "thread_id": state.thread_id,
                "previous_thread_ids": state.previous_thread_ids,
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


def config_fingerprint(
    paths: KeepUpWithPaths,
) -> tuple[tuple[int, int], tuple[int, int]]:
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


if __name__ == "__main__":
    main()

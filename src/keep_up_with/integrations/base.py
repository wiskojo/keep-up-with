from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event as ThreadEvent
from typing import Any, Protocol

from dotenv import set_key

from keep_up_with.core.config import KeepUpWithConfig, KeepUpWithPaths
from keep_up_with.core.events import Event

EventRecorder = Callable[..., Event | None]


@dataclass(frozen=True)
class Subscription:
    name: str
    run: Callable[["SubscriptionContext"], None]
    default_interval_seconds: float | None = None
    baseline_first_run: bool = False


@dataclass(frozen=True)
class IntegrationParameter:
    name: str
    help: str = ""


@dataclass(frozen=True)
class DataIntegration:
    name: str
    description: str = ""
    subscriptions: Sequence[Subscription] = ()
    tools: Sequence["Tool"] = ()
    required_env: Sequence[str] = ()
    parameters: Sequence[IntegrationParameter] = ()
    default_settings: dict[str, Any] = field(default_factory=dict)

    def default_config(self, *, enabled: bool = False) -> dict[str, Any]:
        settings = {**self.default_settings, "enabled": enabled}
        for subscription in self.subscriptions:
            if subscription.default_interval_seconds is not None:
                settings.setdefault(
                    "interval_seconds",
                    int(subscription.default_interval_seconds),
                )
        for parameter in self.parameters:
            settings.setdefault(parameter.name, [])
        return settings


@dataclass(frozen=True)
class MessagingIntegration:
    name: str
    client: Callable[["MessagingContext"], "MessagingClient"]
    subscriptions: Sequence[Subscription] = ()
    required_env: Sequence[str] = ()
    required_settings: Sequence[str] = ()
    setup: Callable[["MessagingSetupContext"], "MessagingSetupResult"] | None = None


@dataclass(frozen=True)
class Tool:
    name: str
    help: str
    function: Callable[..., Any]


def poll_every(
    name: str,
    *,
    default_interval_seconds: float,
) -> Callable[[Callable[["SubscriptionContext"], None]], Subscription]:
    def decorate(poll: Callable[[SubscriptionContext], None]) -> Subscription:
        return Subscription(
            name=name,
            run=poll,
            default_interval_seconds=default_interval_seconds,
            baseline_first_run=True,
        )

    return decorate


def subscription(name: str) -> Callable[[Callable[["SubscriptionContext"], None]], Subscription]:
    def decorate(run: Callable[[SubscriptionContext], None]) -> Subscription:
        return Subscription(name=name, run=run)

    return decorate


def tool(help: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Tool]:
    def decorate(function: Callable[..., Any]) -> Tool:
        return Tool(name=name or function.__name__, help=help, function=function)

    return decorate


@dataclass(frozen=True)
class MessageRef:
    channel_id: str
    message_id: str
    url: str
    thread_id: str | None = None


@dataclass(frozen=True)
class ChannelRef:
    id: str
    name: str
    type: str
    description: str = ""
    section: str = ""
    section_id: str = ""
    position: int = 0


@dataclass(frozen=True)
class SectionRef:
    id: str
    name: str
    position: int = 0


@dataclass(frozen=True)
class ThreadRef:
    id: str
    name: str
    channel_id: str
    url: str = ""


@dataclass(frozen=True)
class ThreadPost:
    text: str
    attachments: Sequence[str] = ()


@dataclass(frozen=True)
class SpaceSection:
    key: str
    name: str


@dataclass(frozen=True)
class SpaceChannel:
    key: str
    name: str
    section: str
    description: str = ""


@dataclass(frozen=True)
class SpacePlan:
    sections: Sequence[SpaceSection] = ()
    channels: Sequence[SpaceChannel] = ()


@dataclass(frozen=True)
class SpaceDeleteItem:
    kind: str
    name: str


@dataclass(frozen=True)
class SpaceResetPreview:
    items: Sequence[SpaceDeleteItem] = ()
    default_empty_server: bool = False
    target: str = ""


class IntegrationContext:
    def __init__(
        self,
        *,
        config: KeepUpWithConfig,
        integration: str,
        settings: dict[str, Any],
    ) -> None:
        self._config = config
        self.integration = integration
        self._settings = settings

    @property
    def workspace(self) -> Path:
        return self._config.paths.workspace

    def env(self, name: str) -> str:
        return self._config.env(name)

    def settings(self) -> dict[str, Any]:
        return self._settings


class ToolContext(IntegrationContext):
    pass


class MessagingContext(IntegrationContext):
    pass


@dataclass
class MessagingSetupContext:
    paths: KeepUpWithPaths
    current: dict[str, Any]
    env_values: dict[str, str]
    ui: Any

    def env(self, name: str) -> str:
        return self.env_values.get(name, "")

    def set_env(self, name: str, value: str) -> None:
        set_key(self.paths.env.as_posix(), name, value)
        self.env_values[name] = value


@dataclass(frozen=True)
class MessagingSetupResult:
    settings: dict[str, Any]


class MessagingClient(Protocol):
    async def list_channels(self) -> list[ChannelRef]: ...

    async def list_sections(self) -> list[SectionRef]: ...

    async def apply_space(self, plan: SpacePlan, *, reset: bool = False) -> None: ...

    async def preview_space_reset(self) -> SpaceResetPreview: ...

    async def create_channel(
        self,
        *,
        name: str,
        section: str | None = None,
        description: str | None = None,
    ) -> ChannelRef: ...

    async def rename_channel(self, *, channel: str, name: str) -> ChannelRef: ...

    async def move_channel(
        self,
        *,
        channel: str,
        section: str | None = None,
        before: str | None = None,
        after: str | None = None,
    ) -> ChannelRef: ...

    async def create_section(self, *, name: str) -> SectionRef: ...

    async def rename_section(self, *, section: str, name: str) -> SectionRef: ...

    async def move_section(
        self,
        *,
        section: str,
        before: str | None = None,
        after: str | None = None,
    ) -> SectionRef: ...

    async def list_messages(
        self,
        *,
        channel: str | None = None,
        thread_id: str | None = None,
        limit: int = 25,
        query: str | None = None,
        author: str | None = None,
    ) -> list[dict[str, Any]]: ...

    async def send_message(
        self,
        *,
        text: str,
        channel: str | None = None,
        thread_id: str | None = None,
        reply_to: str | None = None,
        attachments: list[str] | None = None,
    ) -> MessageRef: ...

    async def edit_message(
        self,
        *,
        message_id: str,
        text: str,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> MessageRef: ...

    async def delete_message(
        self,
        *,
        message_id: str,
        channel: str | None = None,
        thread_id: str | None = None,
    ) -> None: ...

    async def create_thread(
        self,
        *,
        channel: str,
        title: str,
        posts: Sequence[ThreadPost],
        from_message: str | None = None,
    ) -> ThreadRef: ...

    async def delete_thread(self, *, thread_id: str) -> None: ...

    async def list_threads(
        self,
        *,
        channel: str | None = None,
        query: str | None = None,
    ) -> list[ThreadRef]: ...

    async def show_thread(self, *, thread_id: str, limit: int) -> dict[str, Any]: ...


class SubscriptionContext(IntegrationContext):
    def __init__(
        self,
        *,
        config: KeepUpWithConfig,
        record_event: EventRecorder,
        integration: str,
        settings: dict[str, Any],
        stop_event: ThreadEvent | None = None,
    ) -> None:
        super().__init__(
            config=config,
            integration=integration,
            settings=settings,
        )
        self._record_event = record_event
        self._stop_event = stop_event or ThreadEvent()

    def should_stop(self) -> bool:
        return self._stop_event.is_set()

    def wait(self, seconds: float) -> bool:
        return self._stop_event.wait(seconds)

    def emit(
        self,
        *,
        kind: str,
        external_id: str,
        summary: str,
        refs: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        high_priority: bool = False,
        summary_limit: int | None = None,
    ) -> Event | None:
        return self._record_event(
            integration=self.integration,
            kind=kind,
            external_id=external_id,
            summary=summary,
            refs=refs,
            data=data,
            high_priority=high_priority,
            summary_limit=summary_limit,
        )

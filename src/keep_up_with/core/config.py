from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import tomli_w
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


@dataclass(frozen=True)
class KeepUpWithPaths:
    home: Path
    config: Path
    env: Path
    workspace: Path
    logs: Path
    run: Path
    events_db: Path
    thread: Path


@dataclass(frozen=True)
class KeepUpWithConfig:
    paths: KeepUpWithPaths
    settings: "KeepUpWithSettings"
    env_values: dict[str, str]

    def integration(self, name: str) -> dict[str, Any]:
        data = self.settings.integrations.get(name, {})
        return data if isinstance(data, dict) else {}

    def integration_enabled(self, name: str) -> bool:
        return bool(self.integration(name).get("enabled", False))

    def messaging(self) -> "MessagingSettings":
        return self.settings.messaging

    def env(self, name: str) -> str:
        value = os.environ.get(name) or self.env_values.get(name)
        if not value:
            raise ValueError(f"missing environment value: {name}")
        return value

    def has_env(self, name: str) -> bool:
        return bool(os.environ.get(name) or self.env_values.get(name))


class MessagingSettings(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    integration: str = "discord"

    @field_validator("integration", mode="before")
    @classmethod
    def required_integration(cls, value: Any) -> str:
        if value is None or isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError("required")
        text = str(value).strip()
        if not text:
            raise ValueError("required")
        return text


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    thread_name: str = "Main"
    codex_socket: str = "~/.codex/app-server-control/app-server-control.sock"


class KeepUpWithSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSettings = Field(default_factory=AppSettings)
    messaging: MessagingSettings
    integrations: dict[str, dict[str, Any]] = Field(default_factory=dict)


@cache
def get_paths() -> KeepUpWithPaths:
    home = Path(os.environ.get("KEEP_UP_WITH_HOME", "~/.keep-up-with")).expanduser()
    return KeepUpWithPaths(
        home=home,
        config=home / "config.toml",
        env=home / ".env",
        workspace=home / "workspace",
        logs=home / "logs",
        run=home / "run",
        events_db=home / "events.sqlite",
        thread=home / "run" / "thread.json",
    )


@cache
def get_config() -> KeepUpWithConfig:
    return load_config(get_paths())


def load_config(paths: KeepUpWithPaths | None = None) -> KeepUpWithConfig:
    paths = paths or get_paths()
    raw = _read_toml(paths.config)
    try:
        settings = KeepUpWithSettings.model_validate(raw)
    except ValidationError as error:
        raise RuntimeError(f"invalid config: {paths.config}\n{error}") from error
    env = {
        key: value
        for key, value in dotenv_values(paths.env).items()
        if value is not None
    }
    return KeepUpWithConfig(paths=paths, settings=settings, env_values=env)


def write_config(paths: KeepUpWithPaths, settings: KeepUpWithSettings) -> None:
    paths.config.parent.mkdir(parents=True, exist_ok=True)
    target = paths.config
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(tomli_w.dumps(settings.model_dump(mode="json")))
    temporary.replace(target)


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"missing config: {path}; run kuw setup first")
    with path.open("rb") as file:
        data = tomllib.load(file)
    return data if isinstance(data, dict) else {}

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

import typer


def echo_json(value: Any, *, err: bool = False) -> None:
    typer.echo(
        json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True),
        err=err,
    )


def echo_jsonl(values: Any) -> None:
    for value in values:
        echo_json(value)


def fail(message: str, **extra: Any) -> None:
    echo_json({"error": message, **extra}, err=True)
    raise typer.Exit(1)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value

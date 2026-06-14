from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import resolve_path

STAR_HISTORY_URL = "https://api.star-history.com/chart"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
CHART_TYPES = {
    "date": "Date",
    "timeline": "Timeline",
}


@tool("Download a GitHub star history comparison SVG", name="star-history")
def star_history(
    _ctx: ToolContext,
    repos: str,
    output: str,
    chart_type: str = "Date",
) -> dict[str, Any]:
    repo_names = _parse_repos(repos)
    chart = _chart_type(chart_type)
    output_path = _output_path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = httpx.get(
        STAR_HISTORY_URL,
        params={"repos": ",".join(repo_names), "type": chart.lower()},
        follow_redirects=True,
        timeout=30,
        headers={"user-agent": "keep-up-with/0.1"},
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "svg" not in content_type and b"<svg" not in response.content[:200]:
        raise ValueError(f"star-history returned non-SVG content: {content_type}")

    output_path.write_bytes(response.content)
    return {
        "ok": True,
        "type": "github_star_history",
        "repos": repo_names,
        "chart_type": chart,
        "url": str(response.url),
        "output": str(output_path),
    }


def _parse_repos(value: str) -> list[str]:
    repos: list[str] = []
    for part in re.split(r"[\s,]+", value.strip()):
        if not part:
            continue
        repo = _normalize_repo(part)
        if repo not in repos:
            repos.append(repo)
    if not repos:
        raise ValueError("at least one GitHub repo is required")
    return repos


def _normalize_repo(value: str) -> str:
    text = value.strip().removesuffix(".git")
    parsed = urlparse(text)
    if parsed.scheme or parsed.netloc:
        host = parsed.netloc.lower()
        if host not in {"github.com", "www.github.com"}:
            raise ValueError(f"only GitHub repos are supported: {value}")
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise ValueError(f"GitHub URL must include owner and repo: {value}")
        text = f"{parts[0]}/{parts[1].removesuffix('.git')}"
    elif text.startswith("github.com/"):
        parts = [part for part in text.split("/") if part]
        if len(parts) < 3:
            raise ValueError(f"GitHub path must include owner and repo: {value}")
        text = f"{parts[1]}/{parts[2].removesuffix('.git')}"
    text = text.strip("/")
    if not REPO_PATTERN.fullmatch(text):
        raise ValueError(f"repo must be owner/name or a GitHub URL: {value}")
    return text


def _chart_type(value: str) -> str:
    key = value.strip().lower()
    try:
        return CHART_TYPES[key]
    except KeyError as error:
        allowed = ", ".join(sorted(CHART_TYPES.values()))
        raise ValueError(f"chart_type must be one of: {allowed}") from error


def _output_path(value: str) -> Path:
    path = resolve_path(value)
    if path.exists() and path.is_dir():
        return path / "star-history.svg"
    if path.suffix:
        return path
    return path / "star-history.svg"

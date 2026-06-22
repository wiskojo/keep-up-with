from __future__ import annotations

import base64
import hashlib
from html.parser import HTMLParser
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urljoin, urlparse

import httpx
from markitdown import MarkItDown
import websocket

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import resolve_path


@tool("Download a web page and page assets")
def download(
    _ctx: ToolContext,
    url: str,
    output_dir: str,
) -> dict[str, Any]:
    with httpx.Client(
        follow_redirects=True,
        timeout=30,
        headers={"user-agent": "keep-up-with/0.1"},
    ) as client:
        response = client.get(url)
        response.raise_for_status()

        target_dir = resolve_path(output_dir) / f"web-page-{safe_path_part(url)}"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_path = target_dir / "page.html"
        markdown_path = target_dir / "page.md"
        assets_path = target_dir / "assets.json"
        assets_markdown_path = target_dir / "assets.md"
        metadata_path = target_dir / "metadata.json"

        html_path.write_text(response.text, encoding=response.encoding or "utf-8")
        markdown = MarkItDown().convert(str(html_path)).text_content.strip()
        markdown_path.write_text(markdown + "\n", encoding="utf-8")
        candidates = _extract_asset_candidates(response.text, base_url=str(response.url))
        assets = _download_assets(candidates, target_dir=target_dir, client=client)
        assets_path.write_text(json.dumps(assets, indent=2, sort_keys=True) + "\n")
        assets_markdown_path.write_text(_assets_markdown(assets), encoding="utf-8")

    metadata = {
        "type": "web_page",
        "url": url,
        "final_url": str(response.url),
        "status_code": response.status_code,
        "html": str(html_path),
        "markdown": str(markdown_path),
        "assets": str(assets_path),
        "assets_markdown": str(assets_markdown_path),
        "asset_count": len(assets),
        "downloaded_asset_count": sum(1 for asset in assets if asset.get("ok")),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return {"ok": True, "output_dir": str(target_dir), **metadata}


@tool("Capture a full-page screenshot with Chrome")
def screenshot(
    _ctx: ToolContext,
    url: str,
    output: str = "research/artifacts/web/screenshot.png",
    width: int = 1440,
    height: int = 1000,
    wait_ms: int = 1000,
    timeout: float = 30.0,
) -> dict[str, Any]:
    output_path = resolve_path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if _inside_codex_sandbox():
        return {
            "ok": False,
            "error": (
                "Chrome screenshots cannot run inside the Codex sandbox. "
                "Rerun this command outside the sandbox."
            ),
        }
    return _capture_full_page(
        url=url,
        output_path=output_path,
        width=width,
        height=height,
        wait_ms=wait_ms,
        timeout=timeout,
    )


def _capture_full_page(
    *,
    url: str,
    output_path: Path,
    width: int,
    height: int,
    wait_ms: int,
    timeout: float,
) -> dict[str, Any]:
    chrome = _chrome_executable()
    if not chrome:
        raise ValueError(
            "Chrome or Chromium was not found. Set KUW_CHROME to a Chrome executable."
        )

    with tempfile.TemporaryDirectory(prefix="kup-chrome-") as profile:
        process = subprocess.Popen(
            [
                chrome,
                "--headless=new",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-breakpad",
                "--disable-crash-reporter",
                "--hide-scrollbars",
                "--noerrdialogs",
                "--no-default-browser-check",
                "--no-first-run",
                "--remote-allow-origins=*",
                "--remote-debugging-port=0",
                f"--user-data-dir={profile}",
                f"--window-size={width},{height}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            port = _wait_for_debug_port(Path(profile), process, timeout=timeout)
            page_ws_url = _new_page_ws_url(port, url)
            with _CdpClient(page_ws_url, timeout=timeout) as client:
                client.call("Page.enable")
                client.call("Runtime.enable")
                _wait_until_ready(client, timeout=timeout)
                if wait_ms:
                    time.sleep(wait_ms / 1000)
                content = _page_content_size(client)
                screenshot_data = client.call(
                    "Page.captureScreenshot",
                    {
                        "format": "png",
                        "fromSurface": True,
                        "captureBeyondViewport": True,
                        "clip": {
                            "x": 0,
                            "y": 0,
                            "width": content["width"],
                            "height": content["height"],
                            "scale": 1,
                        },
                    },
                )
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    output_path.write_bytes(base64.b64decode(screenshot_data["data"]))
    return {
        "ok": True,
        "url": url,
        "output": str(output_path),
        "viewport": {"width": width, "height": height},
        "image": content,
    }


def _inside_codex_sandbox() -> bool:
    return bool(os.environ.get("CODEX_SANDBOX"))


def _chrome_executable() -> str:
    candidates = [
        os.environ.get("KUW_CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome-stable"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    return ""


def safe_path_part(value: str) -> str:
    parsed = urlparse(value)
    base = f"{parsed.netloc}{parsed.path}".strip("/") or "page"
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-._").lower()
    suffix = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{base[:70] or 'page'}-{suffix}"


class _AssetParser(HTMLParser):
    def __init__(self, *, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.assets: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "img":
            self._add_url(tag=tag, attr="src", values=values, kind="image")
            self._add_srcset(tag=tag, attr="srcset", values=values, kind="image")
        elif tag == "source":
            kind = _asset_kind_from_content_type(values.get("type", ""))
            self._add_url(tag=tag, attr="src", values=values, kind=kind)
            self._add_srcset(tag=tag, attr="srcset", values=values, kind=kind)
        elif tag == "video":
            self._add_url(tag=tag, attr="src", values=values, kind="video")
            self._add_url(tag=tag, attr="poster", values=values, kind="image")
        elif tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key in {"og:image", "og:image:url", "twitter:image", "twitter:image:src"}:
                self._add_url(tag=tag, attr="content", values=values, kind="image")
            elif key in {
                "og:video",
                "og:video:url",
                "og:video:secure_url",
                "twitter:player:stream",
            }:
                self._add_url(tag=tag, attr="content", values=values, kind="video")
        elif tag == "link":
            rel = values.get("rel", "").lower()
            if any(part in {"icon", "apple-touch-icon"} for part in rel.split()):
                self._add_url(tag=tag, attr="href", values=values, kind="image")

    def _add_url(
        self,
        *,
        tag: str,
        attr: str,
        values: dict[str, str],
        kind: str,
        srcset_descriptor: str = "",
    ) -> None:
        raw_url = values.get(attr, "").strip()
        if not raw_url:
            return
        url = _absolute_asset_url(raw_url, base_url=self.base_url)
        if not url:
            return
        self.assets.append(
            {
                "kind": _asset_kind_from_url(url, fallback=kind),
                "url": url,
                "source": f"{tag}[{attr}]",
                "alt": values.get("alt", ""),
                "title": values.get("title", ""),
                "type": values.get("type", ""),
                "media": values.get("media", ""),
                "rel": values.get("rel", ""),
                "property": values.get("property", ""),
                "name": values.get("name", ""),
                "srcset_descriptor": srcset_descriptor,
            }
        )

    def _add_srcset(
        self,
        *,
        tag: str,
        attr: str,
        values: dict[str, str],
        kind: str,
    ) -> None:
        for raw_url, descriptor in _parse_srcset(values.get(attr, "")):
            merged = dict(values)
            merged[attr] = raw_url
            self._add_url(
                tag=tag,
                attr=attr,
                values=merged,
                kind=kind,
                srcset_descriptor=descriptor,
            )


def _extract_asset_candidates(html: str, *, base_url: str) -> list[dict[str, Any]]:
    parser = _AssetParser(base_url=base_url)
    parser.feed(html)
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for asset in parser.assets:
        url = str(asset.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        asset["index"] = len(candidates) + 1
        candidates.append(asset)
    return candidates


def _download_assets(
    candidates: list[dict[str, Any]],
    *,
    target_dir: Path,
    client: httpx.Client,
) -> list[dict[str, Any]]:
    assets_dir = target_dir / "assets"
    if candidates:
        assets_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, Any]] = []
    for candidate in candidates:
        asset = dict(candidate)
        index = int(asset["index"])
        url = str(asset["url"])
        try:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";")[0]
                filename = _asset_filename(
                    index=index,
                    url=url,
                    content_type=content_type,
                    kind=str(asset.get("kind") or "asset"),
                )
                path = assets_dir / filename
                size = 0
                with path.open("wb") as output:
                    for chunk in response.iter_bytes():
                        if not chunk:
                            continue
                        output.write(chunk)
                        size += len(chunk)
            asset.update(
                {
                    "ok": True,
                    "path": str(path),
                    "relative_path": str(path.relative_to(target_dir)),
                    "content_type": content_type,
                    "size_bytes": size,
                }
            )
        except Exception as error:
            asset.update({"ok": False, "error": str(error)})
        assets.append(asset)
    return assets


def _assets_markdown(assets: list[dict[str, Any]]) -> str:
    lines = ["# Assets", ""]
    if not assets:
        lines.extend(["No page assets found.", ""])
        return "\n".join(lines)

    for asset in assets:
        index = int(asset.get("index") or 0)
        kind = str(asset.get("kind") or "asset")
        label = _asset_label(asset)
        lines.append(f"## {index}. {kind}: {label}")
        if asset.get("ok") and asset.get("relative_path"):
            lines.append(f"- File: `{asset['relative_path']}`")
        else:
            lines.append("- File: not downloaded")
        lines.append(f"- URL: {asset.get('url', '')}")
        lines.append(f"- Source: `{asset.get('source', '')}`")
        if asset.get("content_type"):
            lines.append(f"- Content type: `{asset['content_type']}`")
        if asset.get("size_bytes") is not None:
            lines.append(f"- Size: {asset['size_bytes']} bytes")
        if asset.get("error"):
            lines.append(f"- Error: {asset['error']}")
        lines.append("")
    return "\n".join(lines)


def _asset_label(asset: dict[str, Any]) -> str:
    for key in ("alt", "title", "property", "name"):
        value = str(asset.get(key) or "").strip()
        if value:
            return value
    path = unquote(urlparse(str(asset.get("url") or "")).path)
    return Path(path).name or str(asset.get("url") or "")


def _absolute_asset_url(raw_url: str, *, base_url: str) -> str:
    raw_url = raw_url.strip()
    if not raw_url:
        return ""
    lowered = raw_url.lower()
    if lowered.startswith(("data:", "blob:", "javascript:", "mailto:", "tel:")):
        return ""
    parsed = urlparse(urljoin(base_url, raw_url))
    if parsed.scheme not in {"http", "https"}:
        return ""
    return parsed.geturl()


def _parse_srcset(value: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for item in value.split(","):
        parts = item.strip().split()
        if not parts:
            continue
        entries.append((parts[0], " ".join(parts[1:])))
    return entries


def _asset_kind_from_content_type(content_type: str) -> str:
    content_type = content_type.lower()
    if content_type.startswith("video/"):
        return "video"
    if content_type.startswith("image/"):
        return "image"
    return "asset"


def _asset_kind_from_url(url: str, *, fallback: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".mp4", ".mov", ".m4v", ".webm"}:
        return "video"
    if suffix in {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}:
        return "image"
    return fallback


def _asset_filename(*, index: int, url: str, content_type: str, kind: str) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)
    source_name = Path(path).name
    stem = Path(source_name).stem or kind or "asset"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "asset"
    suffix = Path(source_name).suffix.lower()
    if not suffix or len(suffix) > 10:
        suffix = mimetypes.guess_extension(content_type) or ".bin"
    return f"asset-{index:02d}-{stem[:50]}{suffix}"


def _wait_for_debug_port(
    profile: Path,
    process: subprocess.Popen[bytes],
    *,
    timeout: float,
) -> int:
    active_port = profile / "DevToolsActivePort"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Chrome exited before DevTools was ready")
        if active_port.exists():
            lines = active_port.read_text().splitlines()
            if lines:
                return int(lines[0])
        time.sleep(0.05)
    raise RuntimeError("Timed out waiting for Chrome DevTools")


def _new_page_ws_url(port: int, url: str) -> str:
    encoded = quote(url, safe="")
    endpoint = f"http://127.0.0.1:{port}/json/new?{encoded}"
    response = httpx.put(endpoint, timeout=10)
    if response.status_code == 405:
        response = httpx.get(endpoint, timeout=10)
    response.raise_for_status()
    data = response.json()
    return str(data["webSocketDebuggerUrl"])


def _wait_until_ready(client: "_CdpClient", *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = client.call(
            "Runtime.evaluate",
            {"expression": "document.readyState", "returnByValue": True},
        )
        value = state.get("result", {}).get("value")
        if value == "complete":
            return
        time.sleep(0.1)
    raise RuntimeError("Timed out waiting for page load")


def _page_content_size(client: "_CdpClient") -> dict[str, int]:
    metrics = client.call("Page.getLayoutMetrics")
    content = metrics.get("cssContentSize") or metrics["contentSize"]
    return {
        "width": max(1, math.ceil(content["width"])),
        "height": max(1, math.ceil(content["height"])),
    }


class _CdpClient:
    def __init__(self, ws_url: str, *, timeout: float) -> None:
        self._connection = websocket.create_connection(ws_url, timeout=timeout)
        self._next_id = 0

    def __enter__(self) -> "_CdpClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self._connection.close()

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._next_id += 1
        request_id = self._next_id
        self._connection.send(
            json.dumps(
                {
                    "id": request_id,
                    "method": method,
                    "params": params or {},
                }
            )
        )
        while True:
            message = json.loads(self._connection.recv())
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(message["error"].get("message", message["error"]))
            return message.get("result", {})

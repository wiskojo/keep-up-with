from __future__ import annotations

import base64
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import typer
import websocket

from keep_up_with.integrations.base import ToolContext, tool
from keep_up_with.integrations.data.common import resolve_path


@tool("Capture a full-page screenshot")
def screenshot(
    _ctx: ToolContext,
    url: str,
    output: str = typer.Option(
        "research/artifacts/web/screenshot.png",
        "--out",
        "-o",
        help="Output PNG",
    ),
    width: int = typer.Option(
        1440,
        "--width",
        help="Viewport width",
        min=320,
        max=4096,
    ),
    height: int = typer.Option(
        1000,
        "--height",
        help="Viewport height",
        min=320,
        max=4096,
    ),
    wait_ms: int = typer.Option(
        1000,
        "--wait-ms",
        help="Extra wait after page load",
        min=0,
        max=30000,
    ),
    timeout: float = typer.Option(
        30.0,
        "--timeout",
        help="Page load timeout in seconds",
        min=1.0,
        max=300.0,
    ),
) -> dict[str, Any]:
    output_path = resolve_path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
        raise RuntimeError(
            "Chrome or Chromium was not found. Set KUW_CHROME to a Chrome executable."
        )

    with tempfile.TemporaryDirectory(prefix="kuw-chrome-") as profile:
        process = subprocess.Popen(
            [
                chrome,
                "--headless=new",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-gpu",
                "--hide-scrollbars",
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
        "url": url,
        "output": str(output_path),
        "viewport": {"width": width, "height": height},
        "image": content,
    }


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

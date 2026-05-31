from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass, field
from typing import Any

import websocket

DEFAULT_SOCKET = "~/.codex/app-server-control/app-server-control.sock"


@dataclass
class JsonRpcClient:
    url: str = f"unix://{DEFAULT_SOCKET}"
    timeout: float = 30.0
    _socket: Any | None = field(init=False, default=None)
    _next_id: int = field(init=False, default=1)

    def connect(self) -> None:
        if not self.url.startswith(("ws://", "wss://")):
            path = self.url.removeprefix("unix://") or DEFAULT_SOCKET
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect(os.path.expanduser(path))
            connection = websocket.WebSocket(timeout=self.timeout)
            try:
                connection.connect(
                    "ws://localhost/",
                    socket=sock,
                    suppress_origin=True,
                )
            except Exception:
                sock.close()
                raise
            self._socket = connection
            return
        self._socket = websocket.create_connection(
            self.url,
            timeout=self.timeout,
            suppress_origin=True,
        )

    def close(self) -> None:
        if self._socket is None:
            return
        self._socket.close()
        self._socket = None

    def request(self, method: str, params: Any) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self.send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        while True:
            message = self.recv()
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"{method} failed: {message['error']}")
            result = message.get("result")
            return result if isinstance(result, dict) else {}

    def send(self, message: dict[str, Any]) -> None:
        if self._socket is None:
            raise RuntimeError("websocket is not connected")
        self._socket.send(json.dumps(message, separators=(",", ":")))

    def recv(self, *, timeout: float | None = None) -> dict[str, Any]:
        if self._socket is None:
            raise RuntimeError("websocket is not connected")

        previous_timeout = self._socket.gettimeout()
        if timeout is not None:
            self._socket.settimeout(timeout)
        try:
            try:
                payload = self._socket.recv()
            except websocket.WebSocketTimeoutException as error:
                raise socket.timeout from error
        finally:
            if timeout is not None:
                self._socket.settimeout(previous_timeout)

        return json.loads(payload)

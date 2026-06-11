from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CodexDaemonProbe:
    running: bool
    version: str = ""
    detail: str = ""


def probe_codex_daemon() -> CodexDaemonProbe:
    try:
        result = subprocess.run(
            ("codex", "app-server", "daemon", "version"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return CodexDaemonProbe(running=False)
    if result.returncode != 0:
        return CodexDaemonProbe(
            running=False,
            detail=(result.stderr or result.stdout).strip(),
        )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return CodexDaemonProbe(running=True)
    return CodexDaemonProbe(
        running=True,
        version=str(data.get("serverVersion") or data.get("version") or ""),
    )

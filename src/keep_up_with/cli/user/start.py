from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from keep_up_with.core.config import KeepUpWithConfig

STARTUP_CHECK_SECONDS = 0.5


@dataclass(frozen=True)
class Service:
    name: str
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]


@dataclass(frozen=True)
class ServiceResult:
    name: str
    action: str
    pid: int | None
    log: str


def start_services(config: KeepUpWithConfig) -> list[ServiceResult]:
    if not config.paths.config.exists() or not config.paths.workspace.exists():
        raise RuntimeError("run kuw setup first")
    require_codex_daemon()
    config.paths.run.mkdir(parents=True, exist_ok=True)
    config.paths.logs.mkdir(parents=True, exist_ok=True)
    return [start_service(config, gateway_service(config))]


def stop_services(config: KeepUpWithConfig) -> list[ServiceResult]:
    config.paths.run.mkdir(parents=True, exist_ok=True)
    config.paths.logs.mkdir(parents=True, exist_ok=True)
    return [stop_service(config, gateway_service(config))]


def services(config: KeepUpWithConfig) -> tuple[Service, ...]:
    return (gateway_service(config),)


def gateway_service(config: KeepUpWithConfig) -> Service:
    return Service(
        name="gateway",
        command=(sys.executable, "-m", "keep_up_with.runtime.gateway"),
        cwd=config.paths.workspace,
        env=service_env(config),
    )


def require_codex_daemon() -> None:
    result = subprocess.run(
        ("codex", "app-server", "daemon", "version"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(
            "Codex app-server daemon is not running. "
            "Start it with `codex app-server daemon start`, then run `kuw start` again"
            f"{suffix}"
        )


def start_service(config: KeepUpWithConfig, service: Service) -> ServiceResult:
    pid = read_pid(pid_path(config, service))
    if pid is not None and is_running(pid):
        return ServiceResult(service.name, "already running", pid, str(log_path(config, service)))

    pid_path(config, service).unlink(missing_ok=True)
    log = log_path(config, service)
    with log.open("a") as output:
        process = subprocess.Popen(
            service.command,
            cwd=service.cwd,
            env=service.env,
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
    time.sleep(STARTUP_CHECK_SECONDS)
    if process.poll() is not None:
        raise RuntimeError(
            f"{service.name} exited during startup with code "
            f"{process.returncode}; see {log}"
        )
    pid_path(config, service).write_text(str(process.pid))
    return ServiceResult(service.name, "started", process.pid, str(log))


def stop_service(config: KeepUpWithConfig, service: Service) -> ServiceResult:
    path = pid_path(config, service)
    pid = read_pid(path)
    log = str(log_path(config, service))
    if pid is None:
        return ServiceResult(service.name, "not running", None, log)
    if not is_running(pid):
        path.unlink(missing_ok=True)
        return ServiceResult(service.name, "not running", None, log)

    os.kill(pid, signal.SIGTERM)
    for _ in range(50):
        if not is_running(pid):
            path.unlink(missing_ok=True)
            return ServiceResult(service.name, "stopped", pid, log)
        time.sleep(0.1)

    os.kill(pid, signal.SIGKILL)
    path.unlink(missing_ok=True)
    return ServiceResult(service.name, "killed", pid, log)


def read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def is_running(pid: int) -> bool:
    try:
        if os.waitpid(pid, os.WNOHANG)[0] == pid:
            return False
    except ChildProcessError:
        pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def pid_path(config: KeepUpWithConfig, service: Service) -> Path:
    return config.paths.run / f"{service.name}.pid"


def log_path(config: KeepUpWithConfig, service: Service) -> Path:
    return config.paths.logs / f"{service.name}.log"


def service_env(config: KeepUpWithConfig) -> dict[str, str]:
    env = os.environ.copy()
    env["KEEP_UP_WITH_HOME"] = str(config.paths.home)
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env.get('PATH', '')}"
    return env

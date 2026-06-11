from __future__ import annotations

import getpass
import os
import re
import select as select_api
import shutil
import sys
import termios
from collections.abc import Sequence
from dataclasses import dataclass

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


@dataclass(frozen=True)
class Choice[T]:
    label: str
    value: T
    description: str = ""


def header(title: str, detail: str = "") -> None:
    print()
    print(f"{accent(_header_icon(title) or _symbol('step'))} {bold(title)}")
    if detail:
        info(detail)


def info(message: str) -> None:
    print(f"{dim(_symbol('line'))} {message}")


def success(message: str) -> None:
    print(f"{green(_symbol('ok'))} {bold(message)}")


def warning(message: str) -> None:
    print(f"{yellow(_symbol('warn'))} {yellow(message)}")


def danger(message: str) -> None:
    print(f"{red(_symbol('error'))} {bold(red(message))}")


def danger_block(title: str, lines: Sequence[str]) -> None:
    print()
    marker = "⚠️" if _unicode_enabled() else _symbol("error")
    print(f"{red(marker)} {bold(red(title))}")
    for line in lines:
        print(red(f"{_symbol('line')} {line}"))


def error(message: str) -> None:
    print(f"{red(_symbol('error'))} {red(message)}", file=sys.stderr)


def summary(items: Sequence[tuple[str, str]]) -> None:
    width = max((len(label) for label, _ in items), default=0)
    for label, value in items:
        print(f"{dim(_symbol('line'))} {dim(label.ljust(width))}  {bold(value)}")


def prompt(message: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    label = f"{accent(_symbol('prompt'))} {bold(message)}{dim(suffix)} "
    if secret:
        value = _masked_input(label)
    else:
        value = input(label)
    return value.strip() or default


def prompt_cancelable(message: str) -> str | None:
    label = f"{accent(_symbol('prompt'))} {bold(message)} {dim('(Esc goes back)')} "
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        value = input(label)
        return value.strip()
    value = _visible_input(label, cancel_on_escape=True)
    return value.strip() if value is not None else None


def confirm(message: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    label = f"{accent(_symbol('prompt'))} {bold(message)} {dim(f'[{suffix}]')} "
    while True:
        value = input(label).strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        warning("Enter yes or no.")


def pause(message: str = "Press Enter to continue") -> None:
    input(f"{dim(_symbol('line'))} {dim(message)}")


def select[T](title: str, choices: Sequence[Choice[T]], default: T | None = None) -> T:
    if not choices:
        raise ValueError("select requires at least one choice")
    if _interactive_enabled():
        return _interactive_select(title, choices, default)
    return _numbered_select(title, choices, default)


def multiselect[T](
    title: str,
    choices: Sequence[Choice[T]],
    selected: set[T] | None = None,
) -> set[T]:
    if not choices:
        return set()
    defaults = selected or set()
    if _interactive_enabled():
        return _interactive_multiselect(title, choices, defaults)
    return _numbered_multiselect(title, choices, defaults)


def bold(text: str) -> str:
    return _ansi("1", text)


def dim(text: str) -> str:
    return _ansi("2", text)


def yellow(text: str) -> str:
    return _ansi("33", text)


def green(text: str) -> str:
    return _ansi("32", text)


def red(text: str) -> str:
    return _ansi("31", text)


def accent(text: str) -> str:
    return _ansi("36", text)


def _ansi(code: str, text: str) -> str:
    if not _color_enabled():
        return text
    return f"\033[{code}m{text}\033[0m"


def _symbol(name: str) -> str:
    unicode = {
        "step": "◆",
        "line": "│",
        "ok": "✔",
        "warn": "▲",
        "error": "✖",
        "prompt": "?",
    }
    ascii = {
        "step": "*",
        "line": "|",
        "ok": "+",
        "warn": "!",
        "error": "x",
        "prompt": "?",
    }
    return (unicode if _unicode_enabled() else ascii)[name]


def _header_icon(title: str) -> str:
    if not _unicode_enabled():
        return ""
    normalized = title.strip().lower()
    if normalized.endswith("credentials"):
        return "🔑"
    icons = {
        "keep up with setup": "👀",
        "keep-up-with setup": "👀",
        "invite": "🔗",
        "user": "👤",
        "server": "🏠",
        "server layout": "💬",
        "integrations": "🔌",
        "topics": "🧭",
        "subscriptions": "🧭",
        "message space": "💬",
        "reset": "↻",
        "runtime": "⚙️",
        "messaging": "💬",
        "workspace": "📁",
        "workflow": "🧠",
    }
    return icons.get(normalized, "")


def _masked_input(label: str) -> str:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return getpass.getpass(label)

    chars: list[str] = []
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = old[:]
    new[6] = old[6][:]
    new[3] &= ~(termios.ECHO | termios.ICANON)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    print(label, end="", flush=True)
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        while True:
            char = sys.stdin.read(1)
            if char in {"\n", "\r"}:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                print()
                return "".join(chars)
            if char == "\x03":
                raise KeyboardInterrupt
            if char == "\x04":
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                print()
                return "".join(chars)
            if char in {"\x7f", "\b"}:
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
                continue
            if char.isprintable():
                chars.append(char)
                print("*", end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _visible_input(label: str, *, cancel_on_escape: bool = False) -> str | None:
    chars: list[str] = []
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = old[:]
    new[6] = old[6][:]
    new[3] &= ~(termios.ECHO | termios.ICANON)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    print(label, end="", flush=True)
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        while True:
            char = sys.stdin.read(1)
            if char in {"\n", "\r"}:
                print()
                return "".join(chars)
            if char == "\x1b" and cancel_on_escape:
                print()
                return None
            if char == "\x03":
                raise KeyboardInterrupt
            if char == "\x04":
                print()
                return "".join(chars)
            if char in {"\x7f", "\b"}:
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
                continue
            if char.isprintable():
                chars.append(char)
                print(char, end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _color_enabled() -> bool:
    return (
        sys.stdout.isatty()
        and os.environ.get("NO_COLOR") is None
        and os.environ.get("TERM") != "dumb"
    )


def _unicode_enabled() -> bool:
    encoding = (sys.stdout.encoding or "").lower()
    return "utf" in encoding and os.environ.get("KEEP_UP_WITH_ASCII") is None


def _interactive_enabled() -> bool:
    return (
        sys.stdin.isatty() and sys.stdout.isatty() and os.environ.get("TERM") != "dumb"
    )


def _interactive_select[T](
    title: str,
    choices: Sequence[Choice[T]],
    default: T | None,
) -> T:
    index = _default_index(choices, default)
    line_count = 0
    chosen: T | None = None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        _enter_raw_mode(fd, old)
        sys.stdout.write("\033[?25l")
        while True:
            line_count = _render_select(title, choices, index, line_count)
            key = _read_key(fd)
            if key == "up":
                index = (index - 1) % len(choices)
            elif key == "down":
                index = (index + 1) % len(choices)
            elif key == "enter":
                chosen = choices[index].value
                break
            elif key.startswith("digit:"):
                digit = int(key.split(":", 1)[1])
                if 1 <= digit <= len(choices):
                    index = digit - 1
                    chosen = choices[index].value
                    break
            elif key == "ctrl-c":
                raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    label = choices[index].label
    if label.lower() in {"back", "done"}:
        _clear_rendered_lines(line_count)
    else:
        _replace_rendered_lines(line_count, f"{green(_symbol('ok'))} {title}: {label}")
    return chosen if chosen is not None else choices[index].value


def _interactive_multiselect[T](
    title: str,
    choices: Sequence[Choice[T]],
    selected: set[T],
) -> set[T]:
    values = set(selected)
    index = 0
    line_count = 0
    done = False
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        _enter_raw_mode(fd, old)
        sys.stdout.write("\033[?25l")
        while True:
            line_count = _render_multiselect(title, choices, values, index, line_count)
            key = _read_key(fd)
            if key == "up":
                index = (index - 1) % len(choices)
            elif key == "down":
                index = (index + 1) % len(choices)
            elif key == "space":
                _toggle(values, choices[index].value)
            elif key == "enter":
                done = True
                break
            elif key.startswith("digit:"):
                digit = int(key.split(":", 1)[1])
                if 1 <= digit <= len(choices):
                    index = digit - 1
                    _toggle(values, choices[index].value)
            elif key == "ctrl-c":
                raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    if done:
        count = len(values)
        _replace_rendered_lines(
            line_count,
            f"{accent(_header_icon(title) or _symbol('step'))} {bold(title)}\n"
            f"{green(_symbol('ok'))} {count} selected",
        )
    return values


def _default_index[T](choices: Sequence[Choice[T]], default: T | None) -> int:
    return next(
        (i for i, item in enumerate(choices) if item.value == default),
        0,
    )


def _enter_raw_mode(fd: int, current: list) -> None:
    new = current[:]
    new[6] = current[6][:]
    new[3] &= ~(termios.ECHO | termios.ICANON)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSADRAIN, new)


def _render_select[T](
    title: str,
    choices: Sequence[Choice[T]],
    active: int,
    previous_lines: int,
) -> int:
    lines = [
        f"{accent(_header_icon(title) or _symbol('step'))} {bold(title)}",
        f"{dim(_symbol('line'))} {dim('Use arrows, Enter, or number keys')}",
    ]
    lines.extend(_choice_lines(choices, active))
    return _render_lines(lines, previous_lines)


def _render_multiselect[T](
    title: str,
    choices: Sequence[Choice[T]],
    selected: set[T],
    active: int,
    previous_lines: int,
) -> int:
    lines = [
        f"{accent(_header_icon(title) or _symbol('step'))} {bold(title)}",
        f"{dim(_symbol('line'))} {dim('Space toggles, Enter confirms, arrows move')}",
    ]
    for index, choice in enumerate(choices):
        pointer = accent("❯") if index == active else " "
        mark = green("●") if choice.value in selected else dim("○")
        label = bold(choice.label) if index == active else choice.label
        suffix = f" - {dim(choice.description)}" if choice.description else ""
        lines.append(f"{pointer} {mark} {label}{suffix}")
    return _render_lines(lines, previous_lines)


def _choice_lines[T](choices: Sequence[Choice[T]], active: int) -> list[str]:
    lines = []
    for index, choice in enumerate(choices):
        pointer = accent("❯") if index == active else " "
        label = bold(choice.label) if index == active else choice.label
        shortcut = dim(f"{index + 1}.")
        suffix = f" - {dim(choice.description)}" if choice.description else ""
        lines.append(f"{pointer} {shortcut} {label}{suffix}")
    return lines


def _render_lines(lines: Sequence[str], previous_lines: int) -> int:
    width = shutil.get_terminal_size((100, 24)).columns
    if previous_lines:
        sys.stdout.write(f"\033[{previous_lines}A")
    else:
        sys.stdout.write("\n")
    for line in lines:
        sys.stdout.write("\033[2K")
        sys.stdout.write(_truncate(line, width))
        if _color_enabled():
            sys.stdout.write("\033[0m")
        sys.stdout.write("\n")
    sys.stdout.flush()
    return len(lines)


def _replace_rendered_lines(line_count: int, replacement: str) -> None:
    _clear_rendered_lines(line_count)
    print(replacement)


def _clear_rendered_lines(line_count: int) -> None:
    if line_count:
        sys.stdout.write(f"\033[{line_count}A")
        for _ in range(line_count):
            sys.stdout.write("\033[2K\n")
        sys.stdout.write(f"\033[{line_count}A")


def _truncate(line: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(ANSI_ESCAPE_RE.sub("", line)) <= width:
        return line
    parts: list[str] = []
    visible = 0
    position = 0
    for match in ANSI_ESCAPE_RE.finditer(line):
        if match.start() > position:
            text = line[position : match.start()]
            remaining = width - visible
            if remaining <= 0:
                break
            parts.append(text[:remaining])
            visible += min(len(text), remaining)
            if len(text) >= remaining:
                break
        parts.append(match.group())
        position = match.end()
    if visible < width and position < len(line):
        parts.append(line[position : position + width - visible])
    return "".join(parts)


def _toggle[T](values: set[T], value: T) -> None:
    if value in values:
        values.remove(value)
    else:
        values.add(value)


def _read_key(fd: int) -> str:
    key = os.read(fd, 1)
    if key in {b"\n", b"\r"}:
        return "enter"
    if key == b" ":
        return "space"
    if key == b"\x03":
        return "ctrl-c"
    if key.isdigit():
        return f"digit:{key.decode()}"
    if key == b"\x1b":
        sequence = key
        while _stdin_ready(fd, 0.03) and len(sequence) < 8:
            sequence += os.read(fd, 1)
        if sequence in {b"\x1b[A", b"\x1bOA"} or sequence.endswith(b"A"):
            return "up"
        if sequence in {b"\x1b[B", b"\x1bOB"} or sequence.endswith(b"B"):
            return "down"
    return ""


def _stdin_ready(fd: int, timeout: float) -> bool:
    ready, _, _ = select_api.select([fd], [], [], timeout)
    return bool(ready)


def _numbered_select[T](
    title: str,
    choices: Sequence[Choice[T]],
    default: T | None,
) -> T:
    header(title)
    default_index = next(
        (i + 1 for i, item in enumerate(choices) if item.value == default),
        1,
    )
    for index, choice in enumerate(choices, start=1):
        suffix = f" - {choice.description}" if choice.description else ""
        print(
            f"{dim(_symbol('line'))} {accent(str(index) + '.')} "
            f"{choice.label}{dim(suffix)}"
        )
    while True:
        value = prompt("Choose", str(default_index))
        try:
            index = int(value)
        except ValueError:
            warning("Enter a number from the list.")
            continue
        if 1 <= index <= len(choices):
            return choices[index - 1].value
        warning("Enter a number from the list.")


def _numbered_multiselect[T](
    title: str,
    choices: Sequence[Choice[T]],
    selected: set[T],
) -> set[T]:
    header(title)
    for index, choice in enumerate(choices, start=1):
        checked = _symbol("ok") if choice.value in selected else " "
        suffix = f" - {choice.description}" if choice.description else ""
        print(
            f"{dim(_symbol('line'))} [{green(checked)}] "
            f"{accent(str(index) + '.')} {choice.label}{dim(suffix)}"
        )
    info("Enter numbers separated by commas. Leave blank to keep current.")
    while True:
        value = prompt("Choose")
        if not value:
            return set(selected)
        try:
            indexes = {int(item.strip()) for item in value.split(",") if item.strip()}
        except ValueError:
            warning("Enter numbers separated by commas.")
            continue
        if all(1 <= index <= len(choices) for index in indexes):
            return {choices[index - 1].value for index in indexes}
        warning("Enter numbers from the list.")

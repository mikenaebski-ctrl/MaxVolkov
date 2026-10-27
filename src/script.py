"""Load and replay a startup script as if the user typed it."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from .parser import strip_comment
from .shell import Shell


class ScriptError(Exception):
    """Report a script that cannot be read."""


@dataclass(frozen=True)
class ScriptLine:
    """Keep a command with its line number in the script file."""

    number: int
    text: str


@dataclass(frozen=True)
class ScriptReport:
    """Summarize a replay: failed lines and an exit request."""

    errors: int = 0
    exited: bool = False


def load_script(path: str) -> List[ScriptLine]:
    """Read commands, dropping blank lines and comments."""
    try:
        content = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        reason = getattr(error, "strerror", None) or str(error)
        raise ScriptError(f"script: cannot read '{path}': {reason}")
    lines = []
    for number, raw in enumerate(content.splitlines(), start=1):
        text = strip_comment(raw).strip()
        if text:
            lines.append(ScriptLine(number, text))
    return lines


def run_script(
    shell: Shell, lines: List[ScriptLine], emit: Callable[[str], None]
) -> ScriptReport:
    """Show each command and its output; stop only on exit."""
    errors = 0
    for line in lines:
        emit(f"{shell.prompt}{line.text}")
        result = shell.execute(line.text)
        if result.text:
            emit(result.text)
        if result.is_error:
            errors += 1
            emit(f"script: line {line.number}: command failed")
        if result.should_exit:
            return ScriptReport(errors, exited=True)
    if errors:
        emit(f"script: finished with {errors} error(s)")
    return ScriptReport(errors)

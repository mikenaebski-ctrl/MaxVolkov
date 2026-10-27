"""Command responses shared by the shell and its interface."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Carry output text, an error flag, and an optional exit request."""

    text: str = ""
    should_exit: bool = False
    is_error: bool = False

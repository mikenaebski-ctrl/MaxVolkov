"""Command responses shared by the shell and its interface."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Carry output text and an optional request to close the shell."""

    text: str = ""
    should_exit: bool = False

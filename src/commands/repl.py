"""Provide the exit command."""

from typing import TYPE_CHECKING, List

from ..constants import EXIT_ARGUMENTS
from ..errors import CommandError
from ..result import CommandResult

if TYPE_CHECKING:
    from ..shell import Shell


def command_exit(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Close the application when called without arguments."""
    if len(arguments) != EXIT_ARGUMENTS:
        raise CommandError("exit: expected no arguments")
    return CommandResult("exit", should_exit=True)

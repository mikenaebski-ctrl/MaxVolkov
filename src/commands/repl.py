"""Provide the commands required by the first stage."""

from typing import TYPE_CHECKING, List

from ..constants import CD_MAX_ARGUMENTS, EXIT_ARGUMENTS
from ..errors import CommandError
from ..result import CommandResult

if TYPE_CHECKING:
    from ..shell import Shell


def command_ls(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Display the command name and every parsed argument."""
    return CommandResult(f"ls: {arguments!r}")


def command_cd(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Display a path argument without changing any directory."""
    if len(arguments) > CD_MAX_ARGUMENTS:
        raise CommandError("cd: expected at most one path")
    return CommandResult(f"cd: {arguments!r}")


def command_exit(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Close the application when called without arguments."""
    if len(arguments) != EXIT_ARGUMENTS:
        raise CommandError("exit: expected no arguments")
    return CommandResult("exit", should_exit=True)

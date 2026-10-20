"""Provide the commands required by the first stage."""

from ..constants import CD_MAX_ARGUMENTS, EXIT_ARGUMENTS
from ..errors import CommandError
from ..result import CommandResult


def command_ls(arguments: list[str]) -> CommandResult:
    """Display the command name and every parsed argument."""
    return CommandResult(f"ls: {arguments!r}")


def command_cd(arguments: list[str]) -> CommandResult:
    """Display a path argument without changing any directory."""
    if len(arguments) > CD_MAX_ARGUMENTS:
        raise CommandError("cd: expected at most one path")
    return CommandResult(f"cd: {arguments!r}")


def command_exit(arguments: list[str]) -> CommandResult:
    """Close the application when called without arguments."""
    if len(arguments) != EXIT_ARGUMENTS:
        raise CommandError("exit: expected no arguments")
    return CommandResult("exit", should_exit=True)

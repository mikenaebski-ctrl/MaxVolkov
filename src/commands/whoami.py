"""Provide the whoami command."""

from typing import TYPE_CHECKING, List

from ..errors import CommandError
from ..result import CommandResult

if TYPE_CHECKING:
    from ..shell import Shell


def command_whoami(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Print the user name shown in the prompt."""
    if arguments:
        raise CommandError(f"whoami: extra operand '{arguments[0]}'")
    return CommandResult(shell.user)

"""Execute parsed commands without accessing the real OS shell."""

from .commands import COMMANDS
from .constants import (
    DEFAULT_PATH,
    DEFAULT_USER_NAME,
    DEFAULT_VFS_NAME,
)
from .errors import CommandError
from .parser import parse_line
from .result import CommandResult


class Shell:
    """Keep display state and dispatch commands through a registry."""

    def __init__(self, name: str = DEFAULT_VFS_NAME) -> None:
        """Assign the VFS name displayed by the GUI."""
        self.name = name

    @property
    def prompt(self) -> str:
        """Build the prompt for the demonstration VFS."""
        return f"{DEFAULT_USER_NAME}@{self.name}:{DEFAULT_PATH}$ "

    def execute(self, line: str) -> CommandResult:
        """Convert expected parser and command errors into output."""
        try:
            tokens = parse_line(line)
        except ValueError as error:
            return CommandResult(f"error: parse: {error}", is_error=True)
        if not tokens:
            return CommandResult()
        name, *arguments = tokens
        handler = COMMANDS.get(name)
        if handler is None:
            return CommandResult(
                f"error: {name}: command not found", is_error=True
            )
        try:
            return handler(arguments)
        except CommandError as error:
            return CommandResult(f"error: {error}", is_error=True)

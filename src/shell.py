"""Execute parsed commands without accessing the real OS shell."""

from typing import List, Optional

from .commands import COMMANDS
from .constants import DEFAULT_VFS_NAME
from .errors import CommandError
from .parser import parse_line
from .resolve import join_path
from .result import CommandResult
from .user import current_user
from .vfs import Vfs


class Shell:
    """Keep display state and dispatch commands through a registry."""

    def __init__(
        self,
        name: str = DEFAULT_VFS_NAME,
        vfs: Optional[Vfs] = None,
        user: Optional[str] = None,
    ) -> None:
        """Assign the displayed name, the loaded VFS and the user."""
        self.name = name
        self.vfs = vfs
        self.user = user or current_user()
        self.cwd: List[str] = []

    @property
    def prompt(self) -> str:
        """Build the prompt with the current directory."""
        path = join_path(self.cwd)
        return f"{self.user}@{self.name}:{path}$ "

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
            return handler(self, arguments)
        except CommandError as error:
            return CommandResult(f"error: {error}", is_error=True)

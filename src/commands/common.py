"""Helpers shared by the file system commands."""

from typing import TYPE_CHECKING

from ..errors import CommandError
from ..resolve import Resolved, resolve
from ..vfs import Vfs

if TYPE_CHECKING:
    from ..shell import Shell


def require_vfs(shell: "Shell", command: str) -> Vfs:
    """Return the loaded VFS or report that none is loaded."""
    if shell.vfs is None:
        raise CommandError(f"{command}: no VFS loaded")
    return shell.vfs


def find(shell: "Shell", vfs: Vfs, path: str) -> Resolved:
    """Resolve a path relative to the current directory of the shell."""
    return resolve(vfs.root, shell.cwd, path)


"""Provide the service command that inspects the loaded VFS."""

from typing import TYPE_CHECKING, List

from ..constants import (
    SIZE_UNIT,
    VFS_INFO_LIST_FLAG,
    VFS_INFO_MAX_ARGUMENTS,
)
from ..errors import CommandError
from ..result import CommandResult
from ..vfs import VfsDir, VfsFile

if TYPE_CHECKING:
    from ..shell import Shell


def describe_node(path: str, node) -> str:
    """Format one VFS entry for the listing."""
    if isinstance(node, VfsDir):
        return f"{path}/"
    kind = "base64" if node.is_binary else "text"
    return f"{path}  {kind}  {node.size} {SIZE_UNIT}"


def command_vfs_info(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Print VFS statistics; with --list also every path."""
    if len(arguments) > VFS_INFO_MAX_ARGUMENTS:
        raise CommandError("vfs-info: expected at most one option")
    listing = arguments == [VFS_INFO_LIST_FLAG]
    if arguments and not listing:
        raise CommandError(f"vfs-info: unknown option '{arguments[0]}'")
    if shell.vfs is None:
        raise CommandError("vfs-info: no VFS loaded")
    stats = shell.vfs.stats()
    lines = [
        f"vfs: {shell.vfs.name}",
        f"directories: {stats.directories}",
        f"files: {stats.files} ({stats.binaries} binary)",
        f"size: {stats.size} {SIZE_UNIT}",
    ]
    if listing:
        lines += [describe_node(p, n) for p, n in shell.vfs.entries()]
    return CommandResult("\n".join(lines))

"""Create the shell for the given parameters, loading the VFS."""

from dataclasses import dataclass
from typing import List

from .config import Config
from .shell import Shell
from .vfs import VfsError, load_vfs


@dataclass(frozen=True)
class Session:
    """Pair a shell with the messages produced while creating it."""

    shell: Shell
    messages: List[str]
    failed: bool = False


def start_session(config: Config) -> Session:
    """Load the VFS if requested; a failure leaves the shell empty."""
    if config.vfs_path is None:
        return Session(Shell(config.vfs_name), [])
    try:
        vfs = load_vfs(config.vfs_path, config.vfs_name)
    except VfsError as error:
        message = [f"error: {error}"]
        return Session(Shell(config.vfs_name), message, failed=True)
    stats = vfs.stats()
    message = (
        f"vfs: loaded {vfs.name} "
        f"({stats.directories} directories, {stats.files} files)"
    )
    return Session(Shell(vfs.name, vfs), [message])

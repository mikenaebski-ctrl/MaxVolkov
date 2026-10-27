"""Register available command handlers."""

from .repl import command_cd, command_exit, command_ls
from .vfs_info import command_vfs_info

COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
    "vfs-info": command_vfs_info,
}

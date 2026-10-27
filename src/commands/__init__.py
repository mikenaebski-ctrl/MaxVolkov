"""Register available command handlers."""

from .fs import command_cat, command_cd, command_ls
from .mv import command_mv
from .repl import command_exit
from .tree import command_tree
from .vfs_info import command_vfs_info
from .whoami import command_whoami

COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "cat": command_cat,
    "mv": command_mv,
    "tree": command_tree,
    "whoami": command_whoami,
    "exit": command_exit,
    "vfs-info": command_vfs_info,
}

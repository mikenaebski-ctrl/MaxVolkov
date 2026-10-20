"""Register available command handlers."""

from .repl import command_cd, command_exit, command_ls

COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
}

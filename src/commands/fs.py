"""Provide the ls, cd and cat commands."""

from typing import TYPE_CHECKING, List, Set, Tuple

from ..constants import (
    ALL_FLAG,
    BLOCK_SEPARATOR,
    CD_MAX_ARGUMENTS,
    CURRENT_SEGMENT,
    DIRECTORY_SIZE,
    HIDDEN_PREFIX,
    IS_A_DIRECTORY,
    LONG_FLAG,
    LS_FLAGS,
    NOT_A_DIRECTORY,
    PARENT_SEGMENT,
    ROOT_PATH,
    SINGLE,
)
from ..errors import CommandError
from ..resolve import PathError
from ..result import CommandResult
from ..vfs import Node, Vfs, VfsDir, VfsFile
from .common import find, require_vfs
from .options import OptionSpec, Options, parse_options

if TYPE_CHECKING:
    from ..shell import Shell

LS_SPEC = OptionSpec(flags=LS_FLAGS)
NO_OPTIONS = OptionSpec()


def entry_line(name: str, node: Node, long_format: bool) -> str:
    """Format one directory entry, optionally as type, size and name."""
    if not long_format:
        return name
    if isinstance(node, VfsDir):
        return f"d {DIRECTORY_SIZE:>6} {name}"
    return f"- {node.size:>6} {name}"


def list_directory(directory: VfsDir, flags: Set[str]) -> List[str]:
    """List visible entries in name order; -a adds . and .. too."""
    long_format = LONG_FLAG in flags
    names = sorted(directory.children)
    lines = []
    if ALL_FLAG in flags:
        dots = (CURRENT_SEGMENT, PARENT_SEGMENT)
        lines += [entry_line(dot, directory, long_format) for dot in dots]
    else:
        names = [n for n in names if not n.startswith(HIDDEN_PREFIX)]
    for name in names:
        lines.append(entry_line(name, directory.children[name], long_format))
    return lines


def list_target(
    shell: "Shell", vfs: Vfs, target: str, options: Options, titled: bool
) -> Tuple[List[str], bool]:
    """List one operand; a bad operand gives an error line and True."""
    try:
        node = find(shell, vfs, target).node
    except PathError as error:
        message = f"error: ls: cannot access '{target}': {error.reason}"
        return [message], True
    if not isinstance(node, VfsDir):
        return [entry_line(target, node, LONG_FLAG in options.flags)], False
    title = [f"{target}:"] if titled else []
    return title + list_directory(node, options.flags), False


def command_ls(shell: "Shell", arguments: List[str]) -> CommandResult:
    """List directories or name files; keep going after a bad operand."""
    options = parse_options("ls", arguments, LS_SPEC)
    vfs = require_vfs(shell, "ls")
    targets = options.operands or [CURRENT_SEGMENT]
    titled = len(targets) != SINGLE
    parts = [list_target(shell, vfs, t, options, titled) for t in targets]
    blocks = [lines for lines, _ in parts if lines]
    text = BLOCK_SEPARATOR.join("\n".join(lines) for lines in blocks)
    return CommandResult(text, is_error=any(failed for _, failed in parts))


def command_cd(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Change the current directory; without a path go to the root."""
    if len(arguments) > CD_MAX_ARGUMENTS:
        raise CommandError("cd: expected at most one path")
    vfs = require_vfs(shell, "cd")
    target = arguments[0] if arguments else ROOT_PATH
    try:
        found = find(shell, vfs, target)
    except PathError as error:
        raise CommandError(f"cd: {target}: {error.reason}")
    if not isinstance(found.node, VfsDir):
        raise CommandError(f"cd: {target}: {NOT_A_DIRECTORY}")
    shell.cwd = found.parts
    return CommandResult()


def file_text(node: VfsFile) -> str:
    """Return text as stored, or the base64 form of binary data."""
    return node.content.removesuffix("\n")


def cat_target(
    shell: "Shell", vfs: Vfs, target: str
) -> Tuple[str, bool]:
    """Return a file's text, or an error line and True."""
    try:
        node = find(shell, vfs, target).node
    except PathError as error:
        return f"error: cat: {target}: {error.reason}", True
    if isinstance(node, VfsDir):
        return f"error: cat: {target}: {IS_A_DIRECTORY}", True
    return file_text(node), False


def command_cat(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Print files in order; report bad operands without stopping."""
    options = parse_options("cat", arguments, NO_OPTIONS)
    vfs = require_vfs(shell, "cat")
    if not options.operands:
        raise CommandError("cat: missing file operand")
    parts = [cat_target(shell, vfs, t) for t in options.operands]
    text = "\n".join(line for line, _ in parts)
    return CommandResult(text, is_error=any(failed for _, failed in parts))

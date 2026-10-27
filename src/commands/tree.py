"""Provide the tree command."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, List, Optional

from ..constants import (
    ALL_FLAG,
    HIDDEN_PREFIX,
    MIN_TREE_DEPTH,
    SINGLE,
    TREE_BLANK,
    TREE_BRANCH,
    TREE_FLAGS,
    TREE_LAST,
    TREE_PIPE,
    TREE_VALUED,
    CURRENT_SEGMENT,
)
from ..errors import CommandError
from ..resolve import PathError
from ..result import CommandResult
from ..vfs import VfsDir
from .common import find, require_vfs
from .options import OptionSpec, parse_options

if TYPE_CHECKING:
    from ..shell import Shell

TREE_SPEC = OptionSpec(flags=TREE_FLAGS, valued=TREE_VALUED)


@dataclass
class TreeSettings:
    """Display options and the running totals of one drawing."""

    show_hidden: bool
    max_depth: Optional[int]
    directories: int = 0
    files: int = 0


def parse_depth(text: Optional[str]) -> Optional[int]:
    """Convert the -L value; absent means unlimited depth."""
    if text is None:
        return None
    try:
        depth = int(text)
    except ValueError:
        depth = 0
    if depth < MIN_TREE_DEPTH:
        raise CommandError("tree: Invalid level, must be greater than 0")
    return depth


def draw(
    directory: VfsDir, prefix: str, level: int, settings: TreeSettings
) -> Iterator[str]:
    """Yield the lines for one directory and, recursively, below it."""
    names = sorted(directory.children)
    if not settings.show_hidden:
        names = [n for n in names if not n.startswith(HIDDEN_PREFIX)]
    for index, name in enumerate(names):
        last = not names[index + SINGLE:]
        node = directory.children[name]
        yield f"{prefix}{TREE_LAST if last else TREE_BRANCH}{name}"
        if not isinstance(node, VfsDir):
            settings.files += SINGLE
            continue
        settings.directories += SINGLE
        if settings.max_depth is None or level < settings.max_depth:
            indent = prefix + (TREE_BLANK if last else TREE_PIPE)
            yield from draw(node, indent, level + SINGLE, settings)


def plural(count: int, word: str, many: str) -> str:
    """Format a counter such as '1 directory' or '3 directories'."""
    return f"{count} {word if count == SINGLE else many}"


def command_tree(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Draw the tree below a path, then count directories and files."""
    options = parse_options("tree", arguments, TREE_SPEC)
    vfs = require_vfs(shell, "tree")
    if len(options.operands) > SINGLE:
        raise CommandError("tree: expected at most one path")
    settings = TreeSettings(
        ALL_FLAG in options.flags, parse_depth(options.values.get("L"))
    )
    target = options.operands[0] if options.operands else CURRENT_SEGMENT
    try:
        node = find(shell, vfs, target).node
    except PathError as error:
        raise CommandError(f"tree: {target}: {error.reason}")
    lines = [target]
    if isinstance(node, VfsDir):
        lines += draw(node, "", SINGLE, settings)
    summary = (
        f"{plural(settings.directories, 'directory', 'directories')}, "
        f"{plural(settings.files, 'file', 'files')}"
    )
    return CommandResult("\n".join([*lines, "", summary]))

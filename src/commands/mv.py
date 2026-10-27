"""Provide the mv command, which changes the VFS only in memory."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

from ..constants import (
    CURRENT_SEGMENT,
    MIN_MV_OPERANDS,
    MV_FLAGS,
    NO_CLOBBER_FLAG,
    NO_SUCH_ENTRY,
    NOT_A_DIRECTORY,
    PARENT_SEGMENT,
    RESOURCE_BUSY,
    ROOT_PATH,
    SINGLE,
    VERBOSE_FLAG,
)
from ..errors import CommandError
from ..resolve import PathError, join_path, node_at, resolve
from ..result import CommandResult
from ..vfs import Node, Vfs, VfsDir
from .common import find, require_vfs
from .options import Options, OptionSpec, parse_options

if TYPE_CHECKING:
    from ..shell import Shell

MV_SPEC = OptionSpec(flags=MV_FLAGS)


class MoveFailure(Exception):
    """Explain why one source could not be moved."""


@dataclass(frozen=True)
class Target:
    """The receiving directory and, for a rename, the new name."""

    directory: VfsDir
    parts: List[str]
    name: Optional[str] = None


@dataclass(frozen=True)
class Plan:
    """One move with everything needed to check and apply it."""

    source: str
    display: str
    node: Node
    directory: VfsDir
    src_parts: List[str]
    final_parts: List[str]
    existing: Optional[Node]


def missing_destination(shell: "Shell", vfs: Vfs, dst: str) -> Target:
    """Target a name that does not exist yet in an existing folder."""
    head, _, name = dst.rpartition(ROOT_PATH)
    if not name:
        raise PathError(NO_SUCH_ENTRY)
    default = ROOT_PATH if dst.startswith(ROOT_PATH) else CURRENT_SEGMENT
    parent = find(shell, vfs, head or default)
    if not isinstance(parent.node, VfsDir):
        raise PathError(NOT_A_DIRECTORY)
    return Target(parent.node, parent.parts, name)


def locate_destination(shell: "Shell", vfs: Vfs, dst: str) -> Target:
    """Find the receiving folder; an existing folder keeps the names."""
    try:
        found = find(shell, vfs, dst)
    except PathError as error:
        if error.reason != NO_SUCH_ENTRY:
            raise
        return missing_destination(shell, vfs, dst)
    if isinstance(found.node, VfsDir):
        return Target(found.node, found.parts)
    parent_parts = found.parts[:-1]
    parent = node_at(vfs.root, parent_parts)
    return Target(parent, parent_parts, found.parts[-1])


def make_plan(
    shell: "Shell", vfs: Vfs, source: str, target: Target, dst: str
) -> Plan:
    """Resolve one source and work out where it would end up."""
    try:
        found = find(shell, vfs, source)
    except PathError as error:
        raise MoveFailure(f"cannot stat '{source}': {error.reason}")
    base = source.rstrip(ROOT_PATH).rpartition(ROOT_PATH)[2]
    if not found.parts or base in (CURRENT_SEGMENT, PARENT_SEGMENT):
        raise MoveFailure(f"cannot move '{source}': {RESOURCE_BUSY}")
    name = target.name or found.parts[-1]
    display = dst if target.name else f"{dst.rstrip(ROOT_PATH)}/{name}"
    return Plan(
        source,
        display,
        found.node,
        target.directory,
        found.parts,
        [*target.parts, name],
        target.directory.children.get(name),
    )


def placement_problem(plan: Plan) -> Optional[str]:
    """Reject moving onto itself or into its own subtree."""
    if plan.final_parts == plan.src_parts:
        return f"'{plan.source}' and '{plan.display}' are the same file"
    inside = plan.final_parts[: len(plan.src_parts)] == plan.src_parts
    if isinstance(plan.node, VfsDir) and inside:
        return (
            f"cannot move '{plan.source}' to a subdirectory of itself, "
            f"'{plan.display}'"
        )
    return None


def overwrite_problem(plan: Plan) -> Optional[str]:
    """Reject replacing a folder with a file or the reverse."""
    existing = plan.existing
    if existing is None:
        return None
    source_is_dir = isinstance(plan.node, VfsDir)
    if isinstance(existing, VfsDir) and not source_is_dir:
        return f"cannot overwrite directory '{plan.display}' with non-directory"
    if isinstance(existing, VfsDir) and existing.children:
        return f"cannot overwrite '{plan.display}': Directory not empty"
    if not isinstance(existing, VfsDir) and source_is_dir:
        return (
            f"cannot overwrite non-directory '{plan.display}' "
            f"with directory '{plan.source}'"
        )
    return None


def relocate(cwd: List[str], old: List[str], new: List[str]) -> List[str]:
    """Follow the current directory when it was moved or lies inside."""
    if cwd[: len(old)] == old:
        return [*new, *cwd[len(old):]]
    return cwd


def apply_plan(shell: "Shell", vfs: Vfs, plan: Plan) -> None:
    """Detach the node from its parent and attach it at the target."""
    parent = node_at(vfs.root, plan.src_parts[:-1])
    del parent.children[plan.src_parts[-1]]
    name = plan.final_parts[-1]
    plan.node.name = name
    plan.directory.children[name] = plan.node
    shell.cwd = relocate(shell.cwd, plan.src_parts, plan.final_parts)


def move_one(
    shell: "Shell", vfs: Vfs, source: str, target: Target, dst: str,
    options: Options,
) -> str:
    """Move a source; return the verbose line, or raise MoveFailure."""
    plan = make_plan(shell, vfs, source, target, dst)
    problem = placement_problem(plan)
    if problem:
        raise MoveFailure(problem)
    if plan.existing is not None and NO_CLOBBER_FLAG in options.flags:
        return ""
    problem = overwrite_problem(plan)
    if problem:
        raise MoveFailure(problem)
    apply_plan(shell, vfs, plan)
    if VERBOSE_FLAG in options.flags:
        return f"renamed '{source}' -> '{plan.display}'"
    return ""


def valid_cwd(vfs: Vfs, cwd: List[str]) -> List[str]:
    """Return the current directory, or the root if it vanished."""
    try:
        return resolve(vfs.root, [], join_path(cwd)).parts
    except PathError:
        return []


def command_mv(shell: "Shell", arguments: List[str]) -> CommandResult:
    """Rename or move entries inside the in-memory VFS."""
    options = parse_options("mv", arguments, MV_SPEC)
    vfs = require_vfs(shell, "mv")
    operands = options.operands
    if not operands:
        raise CommandError("mv: missing file operand")
    if len(operands) < MIN_MV_OPERANDS:
        raise CommandError(
            f"mv: missing destination file operand after '{operands[0]}'"
        )
    *sources, dst = operands
    try:
        target = locate_destination(shell, vfs, dst)
    except PathError as error:
        raise CommandError(
            f"mv: cannot move '{sources[0]}' to '{dst}': {error.reason}"
        )
    if len(sources) != SINGLE and target.name is not None:
        raise CommandError(f"mv: target '{dst}' is not a directory")
    lines: List[str] = []
    failed = False
    for source in sources:
        try:
            lines.append(move_one(shell, vfs, source, target, dst, options))
        except MoveFailure as error:
            lines.append(f"error: mv: {error}")
            failed = True
    shell.cwd = valid_cwd(vfs, shell.cwd)
    text = "\n".join(line for line in lines if line)
    return CommandResult(text, is_error=failed)

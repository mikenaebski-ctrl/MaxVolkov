"""Resolve UNIX-style paths inside the in-memory VFS."""

from dataclasses import dataclass
from typing import List

from .constants import (
    CURRENT_SEGMENT,
    NO_SUCH_ENTRY,
    NOT_A_DIRECTORY,
    PARENT_SEGMENT,
    ROOT_PATH,
)
from .vfs import Node, VfsDir


class PathError(Exception):
    """Explain why a path does not lead to an entry."""

    def __init__(self, reason: str) -> None:
        """Keep the reason in the UNIX wording."""
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Resolved:
    """An entry together with its absolute path as name segments."""

    parts: List[str]
    node: Node


def step(parts: List[str], nodes: List[Node], segment: str) -> None:
    """Move one segment down, up (..) or stay (.)."""
    if not segment:
        return
    current = nodes[-1]
    if not isinstance(current, VfsDir):
        raise PathError(NOT_A_DIRECTORY)
    if segment == CURRENT_SEGMENT:
        return
    if segment == PARENT_SEGMENT:
        if parts:
            parts.pop()
            nodes.pop()
        return
    child = current.children.get(segment)
    if child is None:
        raise PathError(NO_SUCH_ENTRY)
    parts.append(segment)
    nodes.append(child)


def resolve(root: VfsDir, cwd: List[str], path: str) -> Resolved:
    """Find the entry for an absolute or relative path."""
    if not path:
        raise PathError(NO_SUCH_ENTRY)
    parts: List[str] = []
    nodes: List[Node] = [root]
    start = [] if path.startswith(ROOT_PATH) else cwd
    for segment in [*start, *path.split(ROOT_PATH)]:
        step(parts, nodes, segment)
    return Resolved(parts, nodes[-1])


def join_path(parts: List[str]) -> str:
    """Format name segments as an absolute path."""
    return ROOT_PATH + ROOT_PATH.join(parts)


def node_at(root: VfsDir, parts: List[str]) -> Node:
    """Return the entry at name segments known to exist."""
    node: Node = root
    for part in parts:
        node = node.children[part]
    return node

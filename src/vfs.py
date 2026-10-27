"""Hold a virtual file system in memory, loaded from a ZIP archive."""

import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Tuple, Union
import zipfile
import zlib

from .constants import (
    CURRENT_SEGMENT,
    NUL_CHAR,
    PARENT_SEGMENT,
    ROOT_PATH,
)


class VfsError(Exception):
    """Report an archive that cannot be loaded as a VFS."""


@dataclass
class VfsFile:
    """Store text as is and binary data as a base64 string."""

    name: str
    content: str
    size: int
    is_binary: bool = False


@dataclass
class VfsDir:
    """Store child nodes by name."""

    name: str
    children: Dict[str, "Node"] = field(default_factory=dict)


Node = Union[VfsFile, VfsDir]


@dataclass(frozen=True)
class VfsStats:
    """Count the nodes of a VFS."""

    directories: int
    files: int
    binaries: int
    size: int


class Vfs:
    """Keep the node tree of one loaded archive."""

    def __init__(self, name: str, root: VfsDir) -> None:
        """Store the display name and the root directory."""
        self.name = name
        self.root = root

    def entries(self) -> Iterator[Tuple[str, Node]]:
        """Yield every node below the root as an absolute path."""
        return walk(self.root, "")

    def stats(self) -> VfsStats:
        """Count directories, files, binary files and bytes."""
        nodes = [node for _, node in self.entries()]
        files = [node for node in nodes if isinstance(node, VfsFile)]
        return VfsStats(
            directories=len(nodes) - len(files),
            files=len(files),
            binaries=sum(1 for node in files if node.is_binary),
            size=sum(node.size for node in files),
        )


def walk(directory: VfsDir, prefix: str) -> Iterator[Tuple[str, Node]]:
    """Yield children in name order, directories followed by contents."""
    for name in sorted(directory.children):
        node = directory.children[name]
        path = f"{prefix}{ROOT_PATH}{name}"
        yield path, node
        if isinstance(node, VfsDir):
            yield from walk(node, path)


def make_file(name: str, data: bytes) -> VfsFile:
    """Keep UTF-8 text readable and encode anything else in base64."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = NUL_CHAR
    if NUL_CHAR in text:
        encoded = base64.b64encode(data).decode("ascii")
        return VfsFile(name, encoded, len(data), is_binary=True)
    return VfsFile(name, text, len(data))


def split_member(member: str) -> List[str]:
    """Split an archive path, rejecting paths that leave the root."""
    if member.startswith(ROOT_PATH):
        raise VfsError(f"vfs: unsafe path in archive: '{member}'")
    parts = [p for p in member.split(ROOT_PATH) if p != CURRENT_SEGMENT]
    if PARENT_SEGMENT in parts:
        raise VfsError(f"vfs: unsafe path in archive: '{member}'")
    return [part for part in parts if part]


def child_dir(parent: VfsDir, name: str, member: str) -> VfsDir:
    """Return an existing or new subdirectory, or fail on a clash."""
    child = parent.children.setdefault(name, VfsDir(name))
    if not isinstance(child, VfsDir):
        raise VfsError(f"vfs: file and directory clash at '{member}'")
    return child


def insert(root: VfsDir, member: str, is_dir: bool, data: bytes) -> None:
    """Add one archive entry, creating the parents it needs."""
    parts = split_member(member)
    if not parts:
        return
    directory = root
    for part in parts if is_dir else parts[:-1]:
        directory = child_dir(directory, part, member)
    if is_dir:
        return
    name = parts[-1]
    if isinstance(directory.children.get(name), VfsDir):
        raise VfsError(f"vfs: file and directory clash at '{member}'")
    directory.children[name] = make_file(name, data)


def read_members(path: str) -> List[Tuple[str, bool, bytes]]:
    """Read every entry of the archive into memory."""
    source = Path(path)
    if not source.exists():
        raise VfsError(f"vfs: cannot load '{path}': file not found")
    if not source.is_file():
        raise VfsError(f"vfs: cannot load '{path}': not a file")
    try:
        with zipfile.ZipFile(source) as archive:
            return [
                (info.filename, info.is_dir(), archive.read(info))
                for info in archive.infolist()
            ]
    except (
        zipfile.BadZipFile,
        zlib.error,
        EOFError,
        NotImplementedError,
        RuntimeError,
    ) as error:
        raise VfsError(
            f"vfs: cannot load '{path}': invalid ZIP archive ({error})"
        )
    except OSError as error:
        reason = error.strerror or str(error)
        raise VfsError(f"vfs: cannot load '{path}': {reason}")


def load_vfs(path: str, name: str) -> Vfs:
    """Load a ZIP archive into memory without extracting it."""
    root = VfsDir("")
    for member, is_dir, data in read_members(path):
        insert(root, member, is_dir, data)
    return Vfs(name, root)

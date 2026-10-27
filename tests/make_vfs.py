"""Build test VFS archives on demand; no archives are stored in git.

Usage: python3 tests/make_vfs.py OUTPUT_DIRECTORY
"""

from pathlib import Path
import sys
from typing import Callable, Dict, List, Tuple
import zipfile

FIXED_TIME = (2025, 1, 1, 0, 0, 0)
BINARY_DATA = bytes(range(256))
ARGUMENT_COUNT = 1
USAGE_ERROR = 2
Entry = Tuple[str, bytes]


def write_zip(path: Path, entries: List[Entry], method: int) -> Path:
    """Write entries; a name ending in a slash becomes a directory."""
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.compress_type = method
            archive.writestr(info, data)
    return path


def minimal(path: Path) -> Path:
    """One file in the root."""
    return write_zip(path, [("readme.txt", b"minimal vfs\n")],
                     zipfile.ZIP_DEFLATED)


def empty(path: Path) -> Path:
    """A valid archive without entries."""
    return write_zip(path, [], zipfile.ZIP_DEFLATED)


def several(path: Path) -> Path:
    """Several files, one folder and a name with a space."""
    entries = [
        ("a.txt", b"first file\n"),
        ("b.txt", "второй файл\n".encode("utf-8")),
        ("notes/todo.txt", b"1. write tests\n2. commit\n"),
        ("My Documents/hello.txt", b"hello from a spaced folder\n"),
    ]
    return write_zip(path, entries, zipfile.ZIP_DEFLATED)


def deep(path: Path) -> Path:
    """Four levels of folders, explicit and implicit directories."""
    entries = [
        ("level1/", b""),
        ("level1/one.txt", b"level 1\n"),
        ("level1/level2/two.txt", b"level 2\n"),
        ("level1/level2/level3/three.txt", b"level 3\n"),
        ("level1/level2/level3/level4/four.txt", b"level 4\n"),
        ("level1/empty/", b""),
        ("top.txt", b"top\n"),
    ]
    return write_zip(path, entries, zipfile.ZIP_DEFLATED)


def binary(path: Path) -> Path:
    """A text file and a file with every byte value."""
    entries = [
        ("text.txt", b"plain text\n"),
        ("bin/data.bin", BINARY_DATA),
    ]
    return write_zip(path, entries, zipfile.ZIP_DEFLATED)


def not_a_zip(path: Path) -> Path:
    """A text file that is not an archive."""
    path.write_text("this is not a zip archive\n", encoding="utf-8")
    return path


def truncated(path: Path) -> Path:
    """An archive cut in the middle."""
    source = several(path.with_name("_source.zip"))
    path.write_bytes(source.read_bytes()[:40])
    source.unlink()
    return path


def corrupt(path: Path) -> Path:
    """An archive whose stored data fails the CRC check."""
    write_zip(path, [("data.txt", b"AAAAAAAA")], zipfile.ZIP_STORED)
    raw = path.read_bytes()
    path.write_bytes(raw.replace(b"AAAAAAAA", b"AAAABAAA"))
    return path


def unsafe(path: Path) -> Path:
    """An archive with a path that leaves the root."""
    return write_zip(path, [("../evil.txt", b"x")], zipfile.ZIP_STORED)


def clash(path: Path) -> Path:
    """An archive where a name is both a file and a folder."""
    entries = [("dup", b"file"), ("dup/inner.txt", b"x")]
    return write_zip(path, entries, zipfile.ZIP_STORED)


BUILDERS: Dict[str, Callable[[Path], Path]] = {
    "minimal.zip": minimal,
    "empty.zip": empty,
    "several.zip": several,
    "deep.zip": deep,
    "binary.zip": binary,
    "not_a_zip.zip": not_a_zip,
    "truncated.zip": truncated,
    "corrupt.zip": corrupt,
    "unsafe.zip": unsafe,
    "clash.zip": clash,
}


def create_all(directory: Path) -> Dict[str, Path]:
    """Create every archive in the directory and return the paths."""
    directory.mkdir(parents=True, exist_ok=True)
    return {
        name: builder(directory / name) for name, builder in BUILDERS.items()
    }


def main(argv: List[str]) -> int:
    """Create all archives in the directory given on the command line."""
    if len(argv) != ARGUMENT_COUNT:
        print(__doc__, file=sys.stderr)
        return USAGE_ERROR
    for name in create_all(Path(argv[0])):
        print(f"created {Path(argv[0]) / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

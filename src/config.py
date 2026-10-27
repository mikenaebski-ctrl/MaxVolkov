"""Read command line parameters and describe them for debug output."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from .constants import DEFAULT_VFS_NAME, NOT_SET_TEXT, PROGRAM_NAME


@dataclass(frozen=True)
class Config:
    """Hold the user parameters given at startup."""

    vfs_path: Optional[str] = None
    script_path: Optional[str] = None

    @property
    def vfs_name(self) -> str:
        """Name the VFS after its file, or use the default name."""
        if self.vfs_path:
            return Path(self.vfs_path).name or DEFAULT_VFS_NAME
        return DEFAULT_VFS_NAME


def build_parser() -> argparse.ArgumentParser:
    """Declare the supported command line parameters."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="UNIX shell emulator with a graphical interface.",
    )
    parser.add_argument(
        "--vfs",
        metavar="PATH",
        help="physical path to the VFS",
    )
    parser.add_argument(
        "--script",
        metavar="PATH",
        help="physical path to the startup script",
    )
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> Config:
    """Parse arguments; argparse exits with a message on bad usage."""
    namespace = build_parser().parse_args(argv)
    return Config(vfs_path=namespace.vfs, script_path=namespace.script)


def describe(config: Config) -> List[str]:
    """List every parameter as a debug line."""
    return [
        f"debug: vfs = {config.vfs_path or NOT_SET_TEXT}",
        f"debug: script = {config.script_path or NOT_SET_TEXT}",
    ]

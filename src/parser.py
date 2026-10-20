"""Parse arguments using UNIX quoting rules."""

import shlex


def parse_line(line: str) -> list[str]:
    """Preserve quoted, escaped, and explicitly empty arguments."""
    return shlex.split(line, comments=False, posix=True)

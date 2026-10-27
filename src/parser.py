"""Parse arguments using UNIX quoting rules."""

import shlex

from .constants import COMMENT_CHAR, ESCAPE_CHAR, QUOTE_CHARS, SINGLE_QUOTE


def parse_line(line: str) -> list[str]:
    """Preserve quoted, escaped, and explicitly empty arguments."""
    return shlex.split(line, comments=False, posix=True)


def next_quote(quote: str, char: str) -> str:
    """Return the quote that is open after reading one character."""
    if quote:
        return "" if char == quote else quote
    return char if char in QUOTE_CHARS else ""


def strip_comment(line: str) -> str:
    """Cut a comment that starts with an unquoted hash after a space."""
    quote = ""
    escaped = False
    previous = " "
    for index, char in enumerate(line):
        if escaped:
            escaped = False
        elif char == ESCAPE_CHAR and quote != SINGLE_QUOTE:
            escaped = True
        elif not quote and char == COMMENT_CHAR and previous.isspace():
            return line[:index]
        else:
            quote = next_quote(quote, char)
        previous = char
    return line

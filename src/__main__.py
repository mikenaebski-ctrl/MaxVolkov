"""Start the graphical shell with python3 -m src."""

import sys
from typing import Optional, Sequence

from .config import describe, parse_args
from .constants import EXIT_FAILURE, EXIT_SUCCESS
from .session import start_session


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Print parameters, launch the GUI, explain missing Tk support."""
    config = parse_args(argv)
    for line in describe(config):
        print(line)
    session = start_session(config)
    for message in session.messages:
        print(message, file=sys.stderr if session.failed else sys.stdout)
    try:
        import tkinter as tk
    except ImportError:
        print(
            'tkinter is unavailable. Check: python3 -c "import tkinter"',
            file=sys.stderr,
        )
        return EXIT_FAILURE
    try:
        from .gui import launch

        launch(config, session)
    except tk.TclError as error:
        print(f"Cannot start the GUI: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())

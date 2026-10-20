"""Start the graphical shell with python3 -m src."""

import sys

from .constants import EXIT_FAILURE, EXIT_SUCCESS


def main() -> int:
    """Launch the GUI and explain unavailable Tk support."""
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

        launch()
    except tk.TclError as error:
        print(f"Cannot start the GUI: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())

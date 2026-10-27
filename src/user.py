"""Find the name of the user running the emulator."""

import getpass

from .constants import DEFAULT_USER_NAME


def current_user() -> str:
    """Return the OS user name, or the default if it is unavailable."""
    try:
        return getpass.getuser() or DEFAULT_USER_NAME
    except (KeyError, OSError, ImportError):
        return DEFAULT_USER_NAME

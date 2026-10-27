"""Check the user name lookup and its fallback."""

import unittest
from unittest import mock

from src.shell import Shell
from src.user import current_user


class UserTests(unittest.TestCase):
    """Verify getpass use, fallback and the shell wiring."""

    def test_uses_os_user(self) -> None:
        """Return the name reported by getpass."""
        with mock.patch("getpass.getuser", return_value="dana"):
            self.assertEqual(current_user(), "dana")
            shell = Shell()
            self.assertEqual(shell.execute("whoami").text, "dana")
            self.assertEqual(shell.prompt, "dana@demo-vfs:/$ ")

    def test_fallback(self) -> None:
        """Fall back to student when the lookup fails or is empty."""
        for effect in (OSError, KeyError, ImportError):
            with self.subTest(effect=effect.__name__):
                with mock.patch("getpass.getuser", side_effect=effect):
                    self.assertEqual(current_user(), "student")
        with mock.patch("getpass.getuser", return_value=""):
            self.assertEqual(current_user(), "student")

    def test_explicit_user_wins(self) -> None:
        """A user given to the shell overrides the OS lookup."""
        self.assertEqual(Shell(user="eve").execute("whoami").text, "eve")

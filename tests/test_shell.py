"""Check command execution, diagnostics, and exit behavior."""

import unittest

from src.shell import Shell


class ShellTests(unittest.TestCase):
    """Exercise observable shell behavior without requiring tkinter."""

    def setUp(self) -> None:
        """Create a fresh shell for every test."""
        self.shell = Shell()

    def test_stub_output(self) -> None:
        """Echo every supported argument without changing the prompt."""
        cases = (
            ("ls", "ls: []"),
            ('ls "My Documents" file', "ls: ['My Documents', 'file']"),
            ("cd", "cd: []"),
            ('cd "My Documents"', "cd: ['My Documents']"),
            ("cd ..", "cd: ['..']"),
            ('cd ""', "cd: ['']"),
        )
        before = self.shell.prompt
        for line, expected in cases:
            with self.subTest(line=line):
                result = self.shell.execute(line)
                self.assertEqual(result.text, expected)
                self.assertFalse(result.should_exit)
                self.assertEqual(self.shell.prompt, before)

    def test_invalid_commands(self) -> None:
        """Report unknown commands and invalid argument counts."""
        cases = (
            ("missing", "error: missing: command not found"),
            ("cd a b", "error: cd: expected at most one path"),
            ("exit now", "error: exit: expected no arguments"),
        )
        for line, expected in cases:
            with self.subTest(line=line):
                result = self.shell.execute(line)
                self.assertEqual(result.text, expected)
                self.assertFalse(result.should_exit)

    def test_parse_error_does_not_stop_shell(self) -> None:
        """Accept a valid command after a malformed quoted line."""
        result = self.shell.execute('ls "unfinished')
        self.assertTrue(result.text.startswith("error: parse:"))
        self.assertFalse(result.should_exit)
        self.assertEqual(self.shell.execute("ls").text, "ls: []")

    def test_blank_line(self) -> None:
        """Return no output for an empty input."""
        result = self.shell.execute("   ")
        self.assertEqual(result.text, "")
        self.assertFalse(result.should_exit)

    def test_exit(self) -> None:
        """Request closing the window for a valid exit command."""
        result = self.shell.execute("exit")
        self.assertEqual(result.text, "exit")
        self.assertTrue(result.should_exit)

    def test_custom_vfs_name(self) -> None:
        """Use the shell name in the visible prompt."""
        shell = Shell("training-vfs")
        self.assertEqual(shell.name, "training-vfs")
        self.assertEqual(shell.prompt, "student@training-vfs:/$ ")

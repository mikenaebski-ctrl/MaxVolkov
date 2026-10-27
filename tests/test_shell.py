"""Check command execution, diagnostics, and exit behavior."""

from pathlib import Path
import tempfile
import unittest

import make_vfs
from src.config import Config
from src.session import start_session
from src.shell import Shell


class ShellTests(unittest.TestCase):
    """Exercise observable shell behavior without requiring tkinter."""

    def setUp(self) -> None:
        """Create a fresh shell for every test."""
        self.shell = Shell()

    def test_commands_need_vfs(self) -> None:
        """Report a missing VFS instead of pretending to list files."""
        for line in ("ls", "cd", "cat x", "tree", "vfs-info"):
            with self.subTest(line=line):
                result = self.shell.execute(line)
                self.assertTrue(result.is_error)
                self.assertIn("no VFS loaded", result.text)

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
        self.assertEqual(self.shell.execute("whoami").text, "student")

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


class VfsInfoTests(unittest.TestCase):
    """Check the service command and the session around it."""

    def setUp(self) -> None:
        """Build archives in a temporary directory."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.paths = make_vfs.create_all(Path(folder.name))

    def session(self, name: str):
        """Start a session for one generated archive."""
        config = Config(vfs_path=str(self.paths[name]))
        return start_session(config)

    def test_info_without_vfs(self) -> None:
        """Report that nothing is loaded."""
        result = Shell().execute("vfs-info")
        self.assertEqual(result.text, "error: vfs-info: no VFS loaded")
        self.assertTrue(result.is_error)

    def test_info_statistics(self) -> None:
        """Print the counters of the loaded archive."""
        shell = self.session("binary.zip").shell
        self.assertEqual(
            shell.execute("vfs-info").text,
            "vfs: binary.zip\ndirectories: 1\nfiles: 2 (1 binary)\n"
            "size: 267 B",
        )

    def test_info_list(self) -> None:
        """List every path with its kind and size."""
        shell = self.session("binary.zip").shell
        lines = shell.execute("vfs-info --list").text.splitlines()
        self.assertEqual(lines[4:], [
            "/bin/",
            "/bin/data.bin  base64  256 B",
            "/text.txt  text  11 B",
        ])

    def test_info_bad_options(self) -> None:
        """Reject unknown and extra options."""
        shell = self.session("minimal.zip").shell
        for line in ("vfs-info -x", "vfs-info --list --list"):
            with self.subTest(line=line):
                self.assertTrue(shell.execute(line).is_error)

    def test_session_names_shell_after_file(self) -> None:
        """Show the archive name in the prompt."""
        session = self.session("minimal.zip")
        self.assertFalse(session.failed)
        self.assertIn("minimal.zip", session.shell.prompt)
        self.assertEqual(
            session.messages,
            ["vfs: loaded minimal.zip (0 directories, 1 files)"],
        )

    def test_failed_session_keeps_shell_usable(self) -> None:
        """Report a load error and still accept commands."""
        session = self.session("not_a_zip.zip")
        self.assertTrue(session.failed)
        self.assertTrue(session.messages[0].startswith("error: vfs:"))
        self.assertEqual(
            session.shell.execute("ls").text, "error: ls: no VFS loaded"
        )

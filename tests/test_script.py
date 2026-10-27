"""Check startup script loading, comments, and replay output."""

from pathlib import Path
import tempfile
import unittest

from src.parser import strip_comment
from src.script import ScriptError, load_script, run_script
from src.shell import Shell


class CommentTests(unittest.TestCase):
    """Verify that only unquoted hashes start comments."""

    def test_strip_comment(self) -> None:
        """Cut real comments and keep quoted or escaped hashes."""
        cases = (
            ("# whole line", ""),
            ("ls  # trailing", "ls  "),
            ('ls "a # b"', 'ls "a # b"'),
            ("ls 'a # b'", "ls 'a # b'"),
            ("ls a#b", "ls a#b"),
            (r"ls \# x", r"ls \# x"),
            (r'ls \" # x', r"ls \" "),
        )
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(strip_comment(line), expected)


class ScriptTests(unittest.TestCase):
    """Verify loading and replaying scripts."""

    def write(self, text: str) -> str:
        """Store script text in a temporary file and return its path."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "start.txt"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_load_skips_comments_and_blanks(self) -> None:
        """Keep original line numbers for the remaining commands."""
        path = self.write("# head\n\nls a  # note\n   \ncd b\n")
        lines = load_script(path)
        self.assertEqual([(x.number, x.text) for x in lines],
                         [(3, "ls a"), (5, "cd b")])

    def test_missing_file(self) -> None:
        """Report a missing script as a readable error."""
        with self.assertRaises(ScriptError) as context:
            load_script("/no/such/script.txt")
        self.assertIn(
            "cannot read '/no/such/script.txt'", str(context.exception)
        )

    def test_invalid_encoding(self) -> None:
        """Report a script that is not valid UTF-8."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "bad.txt"
        path.write_bytes(b"\xff\xfe\x00")
        with self.assertRaises(ScriptError):
            load_script(str(path))

    def test_replay_shows_input_and_output(self) -> None:
        """Echo prompt and command, then the command output."""
        shell = Shell()
        out = []
        report = run_script(
            shell, load_script(self.write("whoami\n")), out.append
        )
        self.assertEqual(
            out, ["student@demo-vfs:/$ whoami", "student"]
        )
        self.assertEqual((report.errors, report.exited), (0, False))

    def test_replay_reports_errors_and_continues(self) -> None:
        """Mark failed lines, keep going, and summarize the failures."""
        path = self.write("missing\nwhoami\ncd a b\n")
        out = []
        report = run_script(Shell(), load_script(path), out.append)
        self.assertEqual(report.errors, 2)
        self.assertIn("script: line 1: command failed", out)
        self.assertIn("script: line 3: command failed", out)
        self.assertIn("student", out)
        self.assertEqual(out[-1], "script: finished with 2 error(s)")

    def test_exit_stops_replay(self) -> None:
        """Ignore commands after exit and report the request."""
        out = []
        path = self.write("exit\nwhoami\n")
        report = run_script(Shell(), load_script(path), out.append)
        self.assertTrue(report.exited)
        self.assertNotIn("student", out)

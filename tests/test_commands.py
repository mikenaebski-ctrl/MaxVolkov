"""Check ls, cd, cat, tree and whoami on generated archives."""

from pathlib import Path
import tempfile
import unittest

import make_vfs
from src.config import Config
from src.session import start_session
from src.shell import Shell
from src.vfs import Vfs, VfsDir, VfsFile


class CommandTestCase(unittest.TestCase):
    """Build archives once per test and offer a helper to run commands."""

    def setUp(self) -> None:
        """Create the temporary archives."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.paths = make_vfs.create_all(Path(folder.name))

    def shell(self, archive: str = "rich.zip") -> Shell:
        """Start a shell with the given archive loaded."""
        return start_session(Config(vfs_path=str(self.paths[archive]))).shell

    def run_in(self, shell: Shell, line: str) -> str:
        """Execute a line and return its text."""
        return shell.execute(line).text

    def assert_error(self, shell: Shell, line: str, text: str) -> None:
        """Expect an error result with the exact text."""
        result = shell.execute(line)
        self.assertTrue(result.is_error, line)
        self.assertEqual(result.text, text)


class LsTests(CommandTestCase):
    """The ls command and its modes."""

    def test_root_listing_hides_dotfiles(self) -> None:
        """Plain ls: sorted names, no hidden entries."""
        self.assertEqual(
            self.run_in(self.shell(), "ls"),
            "docs\nempty\nreadme.txt\nsrc",
        )

    def test_all(self) -> None:
        """-a adds hidden entries and the dot entries."""
        self.assertEqual(
            self.run_in(self.shell(), "ls -a"),
            ".\n..\n.hidden\ndocs\nempty\nreadme.txt\nsrc",
        )

    def test_long(self) -> None:
        """-l shows type and size; combined flags work."""
        shell = self.shell()
        self.assertEqual(
            self.run_in(shell, "ls -l docs/img"),
            "- " + f"{8:>6} logo.bin",
        )
        self.assertEqual(
            self.run_in(shell, "ls -la docs"),
            "d      0 .\nd      0 ..\n"
            "- " + f"{7:>6} .secret\n"
            "- " + f"{6:>6} guide.txt\nd      0 img",
        )

    def test_paths(self) -> None:
        """Absolute, relative, dot and dot-dot operands."""
        shell = self.shell()
        self.assertEqual(self.run_in(shell, "ls /docs"), "guide.txt\nimg")
        self.assertEqual(
            self.run_in(shell, "ls docs/img/.."), "guide.txt\nimg"
        )
        self.assertEqual(
            self.run_in(shell, "ls /.."), self.run_in(shell, "ls")
        )
        self.run_in(shell, "cd src")
        self.assertEqual(self.run_in(shell, "ls ."), "lib\nmain.py")
        self.assertEqual(self.run_in(shell, "ls ../docs"), "guide.txt\nimg")

    def test_file_operand(self) -> None:
        """A file operand prints its name."""
        self.assertEqual(
            self.run_in(self.shell(), "ls readme.txt"), "readme.txt"
        )

    def test_empty_directory(self) -> None:
        """An empty folder lists nothing and is not an error."""
        result = self.shell().execute("ls empty")
        self.assertEqual(result.text, "")
        self.assertFalse(result.is_error)

    def test_several_operands_and_errors(self) -> None:
        """Titles per operand; a bad one does not hide the others."""
        result = self.shell().execute("ls docs nothing src/lib")
        self.assertEqual(
            result.text,
            "docs:\nguide.txt\nimg\n\n"
            "error: ls: cannot access 'nothing': No such file or directory"
            "\n\nsrc/lib:\nutil.py",
        )
        self.assertTrue(result.is_error)

    def test_errors(self) -> None:
        """Missing path, file used as directory, empty path, bad option."""
        shell = self.shell()
        self.assert_error(
            shell, "ls nothing",
            "error: ls: cannot access 'nothing': No such file or directory",
        )
        self.assert_error(
            shell, "ls readme.txt/x",
            "error: ls: cannot access 'readme.txt/x': Not a directory",
        )
        self.assert_error(
            shell, 'ls ""',
            "error: ls: cannot access '': No such file or directory",
        )
        self.assert_error(shell, "ls -z", "error: ls: invalid option -- 'z'")

    def test_end_of_options(self) -> None:
        """-- lets an operand start with a dash."""
        self.assert_error(
            self.shell(), "ls -- -l",
            "error: ls: cannot access '-l': No such file or directory",
        )


class CdTests(CommandTestCase):
    """The cd command and the prompt."""

    def test_cd_changes_prompt(self) -> None:
        """Relative, absolute, parent and root moves."""
        shell = self.shell()
        self.run_in(shell, "cd docs/img")
        self.assertEqual(shell.prompt, "student@rich.zip:/docs/img$ ")
        self.run_in(shell, "cd ..")
        self.assertEqual(shell.prompt, "student@rich.zip:/docs$ ")
        self.run_in(shell, "cd /src/lib")
        self.assertEqual(shell.prompt, "student@rich.zip:/src/lib$ ")
        self.run_in(shell, "cd")
        self.assertEqual(shell.prompt, "student@rich.zip:/$ ")

    def test_parent_of_root_is_root(self) -> None:
        """Going above the root stays in the root."""
        shell = self.shell()
        self.run_in(shell, "cd ../..")
        self.assertEqual(shell.prompt, "student@rich.zip:/$ ")

    def test_quoted_name_with_space(self) -> None:
        """A quoted name with a space is one operand."""
        shell = self.shell("several.zip")
        self.run_in(shell, 'cd "My Documents"')
        self.assertEqual(self.run_in(shell, "ls"), "hello.txt")
        self.assertIn("/My Documents$", shell.prompt)

    def test_errors_keep_directory(self) -> None:
        """A failed cd leaves the current directory unchanged."""
        shell = self.shell()
        self.run_in(shell, "cd docs")
        self.assert_error(
            shell, "cd nothing",
            "error: cd: nothing: No such file or directory",
        )
        self.assert_error(
            shell, "cd guide.txt", "error: cd: guide.txt: Not a directory"
        )
        self.assert_error(
            shell, "cd a b", "error: cd: expected at most one path"
        )
        self.assertIn(":/docs$", shell.prompt)


class CatTests(CommandTestCase):
    """The cat command."""

    def test_text_file(self) -> None:
        """Print a file without the trailing newline duplicated."""
        self.assertEqual(
            self.run_in(self.shell(), "cat readme.txt"),
            "Rich VFS\nsecond line",
        )

    def test_several_files(self) -> None:
        """Concatenate files in the given order."""
        self.assertEqual(
            self.run_in(self.shell(), "cat docs/guide.txt .hidden"),
            "guide\nhidden file",
        )

    def test_binary_file_as_base64(self) -> None:
        """Binary data is shown in base64."""
        self.assertEqual(
            self.run_in(self.shell(), "cat docs/img/logo.bin"), "AAECAwQFBgc="
        )

    def test_unicode(self) -> None:
        """Non-ASCII text survives."""
        self.assertEqual(
            self.run_in(self.shell("several.zip"), "cat b.txt"),
            "второй файл",
        )

    def test_errors(self) -> None:
        """Missing operand, missing file, directory, partial output."""
        shell = self.shell()
        self.assert_error(shell, "cat", "error: cat: missing file operand")
        self.assert_error(
            shell, "cat nothing",
            "error: cat: nothing: No such file or directory",
        )
        self.assert_error(
            shell, "cat docs", "error: cat: docs: Is a directory"
        )
        self.assert_error(
            shell, "cat readme.txt docs",
            "Rich VFS\nsecond line\nerror: cat: docs: Is a directory",
        )

    def test_file_text_resembling_error_is_not_an_error(self) -> None:
        """Only real failures set the error flag."""
        root = VfsDir("", {"note": VfsFile("note", "error: text\n", 12)})
        shell = Shell("x", Vfs("x", root))
        result = shell.execute("cat note")
        self.assertEqual(result.text, "error: text")
        self.assertFalse(result.is_error)


class TreeTests(CommandTestCase):
    """The tree command."""

    def test_full_tree(self) -> None:
        """Draw connectors and count entries; hidden entries are skipped."""
        self.assertEqual(
            self.run_in(self.shell(), "tree"),
            ".\n"
            "├── docs\n"
            "│   ├── guide.txt\n"
            "│   └── img\n"
            "│       └── logo.bin\n"
            "├── empty\n"
            "├── readme.txt\n"
            "└── src\n"
            "    ├── lib\n"
            "    │   └── util.py\n"
            "    └── main.py\n"
            "\n"
            "5 directories, 5 files",
        )

    def test_all_flag(self) -> None:
        """-a shows hidden entries."""
        text = self.run_in(self.shell(), "tree -a docs")
        self.assertEqual(
            text,
            "docs\n├── .secret\n├── guide.txt\n└── img\n"
            "    └── logo.bin\n\n1 directory, 3 files",
        )

    def test_depth(self) -> None:
        """-L limits the depth; attached and separate values work."""
        shell = self.shell()
        expected = (
            ".\n├── docs\n├── empty\n├── readme.txt\n└── src\n\n"
            "3 directories, 1 file"
        )
        self.assertEqual(self.run_in(shell, "tree -L 1"), expected)
        self.assertEqual(self.run_in(shell, "tree -L1"), expected)

    def test_subdirectory_file_and_empty(self) -> None:
        """Operands: a folder, a file and an empty folder."""
        shell = self.shell()
        self.assertEqual(
            self.run_in(shell, "tree src/lib"),
            "src/lib\n└── util.py\n\n0 directories, 1 file",
        )
        self.assertEqual(
            self.run_in(shell, "tree readme.txt"),
            "readme.txt\n\n0 directories, 0 files",
        )
        self.assertEqual(
            self.run_in(shell, "tree empty"), "empty\n\n0 directories, 0 files"
        )

    def test_errors(self) -> None:
        """Bad depth, bad path, too many operands."""
        shell = self.shell()
        for line in ("tree -L 0", "tree -L x"):
            self.assert_error(
                shell, line,
                "error: tree: Invalid level, must be greater than 0",
            )
        self.assert_error(
            shell, "tree -L",
            "error: tree: option requires an argument -- 'L'",
        )
        self.assert_error(
            shell, "tree nothing",
            "error: tree: nothing: No such file or directory",
        )
        self.assert_error(
            shell, "tree a b", "error: tree: expected at most one path"
        )


class WhoamiTests(CommandTestCase):
    """The whoami command, which needs no VFS."""

    def test_whoami(self) -> None:
        """Print the user; reject operands."""
        shell = Shell()
        self.assertEqual(self.run_in(shell, "whoami"), "student")
        self.assert_error(
            shell, "whoami now", "error: whoami: extra operand 'now'"
        )

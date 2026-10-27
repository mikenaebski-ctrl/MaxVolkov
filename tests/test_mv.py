"""Check mv: renames, moves, overwrites, errors and in-memory only."""

from pathlib import Path
import tempfile
from typing import Dict, Union
import unittest

import make_vfs
from src.config import Config
from src.session import start_session
from src.shell import Shell
from src.vfs import Vfs, VfsDir, VfsFile

Spec = Dict[str, Union[str, dict]]


def build(spec: Spec) -> VfsDir:
    """Create a directory tree from nested dictionaries."""
    directory = VfsDir("")
    for name, value in spec.items():
        if isinstance(value, dict):
            child = build(value)
            child.name = name
        else:
            child = VfsFile(name, value, len(value))
        directory.children[name] = child
    return directory


class MvTestCase(unittest.TestCase):
    """Helpers to run commands against generated or built trees."""

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
        """Expect an error result with exactly this text."""
        result = shell.execute(line)
        self.assertTrue(result.is_error, line)
        self.assertEqual(result.text, text)

    def collision_shell(self) -> Shell:
        """A tree with name clashes for the overwrite rules."""
        root = build({
            "a": {"x": {"f": "1"}},
            "b": {"x": {"g": "2"}, "d": "file in b"},
            "e": {"x": {}},
            "x": "top file",
            "d": {"h": "3"},
        })
        return Shell("t", Vfs("t", root))


class MoveTests(MvTestCase):
    """Successful moves."""

    def test_rename_file(self) -> None:
        """A new name in the same folder."""
        shell = self.shell()
        result = shell.execute("mv readme.txt notes.txt")
        self.assertEqual((result.text, result.is_error), ("", False))
        self.assertEqual(
            self.run_in(shell, "ls"), "docs\nempty\nnotes.txt\nsrc"
        )
        self.assertEqual(
            self.run_in(shell, "cat notes.txt"), "Rich VFS\nsecond line"
        )
        self.assertEqual(shell.vfs.root.children["notes.txt"].name, "notes.txt")

    def test_move_into_directory(self) -> None:
        """An existing folder receives the file under the same name."""
        shell = self.shell()
        self.run_in(shell, "mv readme.txt docs")
        self.assertEqual(
            self.run_in(shell, "ls docs"), "guide.txt\nimg\nreadme.txt"
        )
        self.assertNotIn("readme.txt", self.run_in(shell, "ls"))

    def test_rename_directory_keeps_contents(self) -> None:
        """A renamed folder keeps all its children."""
        shell = self.shell()
        self.run_in(shell, "mv src code")
        self.assertEqual(
            self.run_in(shell, "tree code"),
            "code\n├── lib\n│   └── util.py\n└── main.py\n\n"
            "1 directory, 2 files",
        )
        self.assertEqual(
            self.run_in(shell, "ls"), "code\ndocs\nempty\nreadme.txt"
        )

    def test_move_directory_into_directory(self) -> None:
        """A folder moves into another with its subtree."""
        shell = self.shell()
        self.run_in(shell, "mv src docs/img")
        self.assertEqual(
            self.run_in(shell, "cat docs/img/src/lib/util.py"), "# util"
        )

    def test_multiple_sources_including_hidden(self) -> None:
        """Several sources go into one folder."""
        shell = self.shell()
        self.run_in(shell, "mv readme.txt .hidden empty docs")
        self.assertEqual(self.run_in(shell, "ls -a /"), ".\n..\ndocs\nsrc")
        self.assertEqual(
            self.run_in(shell, "ls -a docs"),
            ".\n..\n.hidden\n.secret\nempty\nguide.txt\nimg\nreadme.txt",
        )

    def test_overwrite_file(self) -> None:
        """A file replaces an existing file."""
        shell = self.shell()
        self.run_in(shell, "mv docs/guide.txt readme.txt")
        self.assertEqual(self.run_in(shell, "cat readme.txt"), "guide")
        self.assertEqual(self.run_in(shell, "ls docs"), "img")
        self.assertEqual(shell.vfs.stats().files, 6)

    def test_paths_with_dots_and_quotes(self) -> None:
        """Relative paths, .. and quoted names."""
        shell = self.shell("several.zip")
        self.run_in(shell, 'mv "My Documents/hello.txt" notes/../hi.txt')
        self.assertEqual(
            self.run_in(shell, "cat hi.txt"), "hello from a spaced folder"
        )
        self.run_in(shell, "cd notes")
        self.run_in(shell, "mv ../a.txt .")
        self.assertEqual(self.run_in(shell, "ls"), "a.txt\ntodo.txt")

    def test_verbose_and_no_clobber(self) -> None:
        """-v reports each move; -n skips existing targets silently."""
        shell = self.shell()
        self.assertEqual(
            self.run_in(shell, "mv -v readme.txt docs"),
            "renamed 'readme.txt' -> 'docs/readme.txt'",
        )
        self.assertEqual(
            self.run_in(shell, "mv -v docs/readme.txt /new"),
            "renamed 'docs/readme.txt' -> '/new'",
        )
        self.run_in(shell, "mv src/lib/util.py docs")
        result = shell.execute("mv -n new docs/util.py")
        self.assertEqual((result.text, result.is_error), ("", False))
        self.assertEqual(self.run_in(shell, "cat docs/util.py"), "# util")

    def test_into_root_with_trailing_slash(self) -> None:
        """A trailing slash on an existing folder is accepted."""
        shell = self.shell()
        self.run_in(shell, "mv docs/guide.txt /empty/")
        self.assertEqual(self.run_in(shell, "ls empty"), "guide.txt")

    def test_overwriting_empty_directory(self) -> None:
        """A folder replaces an empty folder of the same name."""
        shell = self.collision_shell()
        self.assertEqual(self.run_in(shell, "mv a/x e"), "")
        self.assertEqual(self.run_in(shell, "ls e/x"), "f")

    def test_state_changes_only_in_memory(self) -> None:
        """The archive on disk is untouched and a reload sees no move."""
        path = self.paths["rich.zip"]
        before = path.read_bytes()
        shell = self.shell()
        self.run_in(shell, "mv src code")
        self.assertEqual(path.read_bytes(), before)
        fresh = self.shell()
        self.assertIn("src", self.run_in(fresh, "ls"))
        self.assertEqual(shell.vfs.stats(), fresh.vfs.stats())


class CwdTests(MvTestCase):
    """The current directory follows a moved folder."""

    def test_moving_current_directory(self) -> None:
        """Renaming the folder we stand in updates the prompt."""
        shell = self.shell()
        self.run_in(shell, "cd docs/img")
        self.run_in(shell, "mv /docs/img /top")
        self.assertEqual(shell.prompt, f"{shell.user}@rich.zip:/top$ ")
        self.assertEqual(self.run_in(shell, "ls"), "logo.bin")

    def test_moving_an_ancestor(self) -> None:
        """Moving a parent keeps the relative position."""
        shell = self.shell()
        self.run_in(shell, "cd docs/img")
        self.run_in(shell, "mv /docs /src")
        self.assertEqual(shell.prompt, f"{shell.user}@rich.zip:/src/docs/img$ ")

    def test_unrelated_move_keeps_directory(self) -> None:
        """Other moves leave the position alone."""
        shell = self.shell()
        self.run_in(shell, "cd docs")
        self.run_in(shell, "mv /readme.txt /src")
        self.assertIn(":/docs$", shell.prompt)


class ErrorTests(MvTestCase):
    """Rejected moves leave the tree unchanged."""

    def test_operand_errors(self) -> None:
        """Missing operands and bad options."""
        shell = self.shell()
        self.assert_error(shell, "mv", "error: mv: missing file operand")
        self.assert_error(
            shell, "mv readme.txt",
            "error: mv: missing destination file operand after 'readme.txt'",
        )
        self.assert_error(
            shell, "mv -z a b", "error: mv: invalid option -- 'z'"
        )

    def test_missing_source(self) -> None:
        """A source that does not exist."""
        self.assert_error(
            self.shell(), "mv nothing docs",
            "error: mv: cannot stat 'nothing': No such file or directory",
        )

    def test_bad_destinations(self) -> None:
        """Missing parent, file as parent, trailing slash on a new name."""
        shell = self.shell()
        self.assert_error(
            shell, "mv readme.txt nothing/x",
            "error: mv: cannot move 'readme.txt' to 'nothing/x': "
            "No such file or directory",
        )
        self.assert_error(
            shell, "mv src readme.txt/x",
            "error: mv: cannot move 'src' to 'readme.txt/x': Not a directory",
        )
        self.assert_error(
            shell, "mv readme.txt fresh/",
            "error: mv: cannot move 'readme.txt' to 'fresh/': "
            "No such file or directory",
        )

    def test_multiple_sources_need_directory(self) -> None:
        """More than one source requires an existing folder."""
        shell = self.shell()
        self.assert_error(
            shell, "mv readme.txt .hidden newname",
            "error: mv: target 'newname' is not a directory",
        )
        self.assert_error(
            shell, "mv readme.txt .hidden src/main.py",
            "error: mv: target 'src/main.py' is not a directory",
        )

    def test_same_file_and_own_subtree(self) -> None:
        """No move onto itself or into itself."""
        shell = self.shell()
        self.assert_error(
            shell, "mv readme.txt readme.txt",
            "error: mv: 'readme.txt' and 'readme.txt' are the same file",
        )
        self.assert_error(
            shell, "mv src/lib src",
            "error: mv: 'src/lib' and 'src/lib' are the same file",
        )
        self.assert_error(
            shell, "mv src src/lib",
            "error: mv: cannot move 'src' to a subdirectory of itself, "
            "'src/lib/src'",
        )
        self.assert_error(
            shell, "mv src src/newname",
            "error: mv: cannot move 'src' to a subdirectory of itself, "
            "'src/newname'",
        )
        self.assertEqual(self.run_in(shell, "ls src"), "lib\nmain.py")

    def test_root_and_dot_sources(self) -> None:
        """The root and . or .. are busy."""
        shell = self.shell()
        self.assert_error(
            shell, "mv / docs",
            "error: mv: cannot move '/': Device or resource busy",
        )
        self.run_in(shell, "cd docs")
        for source in (".", "..", "../docs/."):
            with self.subTest(source=source):
                self.assertTrue(shell.execute(f"mv {source} /src").is_error)
        self.assertIn(":/docs$", shell.prompt)

    def test_overwrite_rules(self) -> None:
        """Folder and file clashes keep both sides unchanged."""
        shell = self.collision_shell()
        self.assert_error(
            shell, "mv a/x b",
            "error: mv: cannot overwrite 'b/x': Directory not empty",
        )
        self.assert_error(
            shell, "mv x a",
            "error: mv: cannot overwrite directory 'a/x' with non-directory",
        )
        self.assert_error(
            shell, "mv d b",
            "error: mv: cannot overwrite non-directory 'b/d' "
            "with directory 'd'",
        )
        self.assertEqual(self.run_in(shell, "ls a/x"), "f")

    def test_partial_failure_moves_the_rest(self) -> None:
        """A bad source does not stop the others."""
        shell = self.shell()
        result = shell.execute("mv readme.txt nothing .hidden docs")
        self.assertTrue(result.is_error)
        self.assertEqual(
            result.text,
            "error: mv: cannot stat 'nothing': No such file or directory",
        )
        self.assertEqual(self.run_in(shell, "ls -a"), ".\n..\ndocs\nempty\nsrc")

    def test_no_vfs(self) -> None:
        """mv needs a loaded VFS."""
        self.assert_error(Shell(), "mv a b", "error: mv: no VFS loaded")

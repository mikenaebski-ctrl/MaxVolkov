"""Check loading ZIP archives into the in-memory VFS."""

import base64
from pathlib import Path
import tempfile
import unittest

import make_vfs
from src.vfs import VfsDir, VfsError, VfsFile, load_vfs


class VfsTestCase(unittest.TestCase):
    """Create the archives in a temporary directory for each test."""

    def setUp(self) -> None:
        """Build every test archive."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.dir = Path(folder.name)
        self.paths = make_vfs.create_all(self.dir)

    def load(self, name: str):
        """Load one of the generated archives."""
        return load_vfs(str(self.paths[name]), name)

    def paths_of(self, name: str) -> list:
        """List the VFS paths of an archive."""
        return [path for path, _ in self.load(name).entries()]


class LoadTests(VfsTestCase):
    """Valid archives of different shapes."""

    def test_minimal(self) -> None:
        """One file in the root."""
        vfs = self.load("minimal.zip")
        self.assertEqual(self.paths_of("minimal.zip"), ["/readme.txt"])
        node = vfs.root.children["readme.txt"]
        self.assertEqual(node.content, "minimal vfs\n")
        self.assertFalse(node.is_binary)

    def test_empty_archive(self) -> None:
        """A valid archive without entries gives an empty root."""
        self.assertEqual(self.paths_of("empty.zip"), [])

    def test_several_files(self) -> None:
        """Files, folders, spaces and Unicode text."""
        self.assertEqual(
            self.paths_of("several.zip"),
            [
                "/My Documents",
                "/My Documents/hello.txt",
                "/a.txt",
                "/b.txt",
                "/notes",
                "/notes/todo.txt",
            ],
        )
        self.assertEqual(
            self.load("several.zip").root.children["b.txt"].content,
            "второй файл\n",
        )

    def test_deep_tree(self) -> None:
        """Four levels, explicit and implicit directories, empty folder."""
        paths = self.paths_of("deep.zip")
        self.assertIn("/level1/level2/level3/level4/four.txt", paths)
        self.assertIn("/level1/empty", paths)
        vfs = self.load("deep.zip")
        self.assertIsInstance(vfs.root.children["level1"], VfsDir)
        self.assertEqual(vfs.stats().directories, 5)
        self.assertEqual(vfs.stats().files, 5)

    def test_binary_is_base64(self) -> None:
        """Non-text data is kept as base64 and decodes back exactly."""
        vfs = self.load("binary.zip")
        node = vfs.root.children["bin"].children["data.bin"]
        self.assertIsInstance(node, VfsFile)
        self.assertTrue(node.is_binary)
        self.assertEqual(
            base64.b64decode(node.content), make_vfs.BINARY_DATA
        )
        self.assertEqual(node.size, len(make_vfs.BINARY_DATA))
        self.assertEqual(vfs.stats().binaries, 1)

    def test_archive_is_not_modified(self) -> None:
        """Loading leaves the archive and its folder untouched."""
        path = self.paths["deep.zip"]
        before = path.read_bytes()
        names = sorted(p.name for p in self.dir.iterdir())
        self.load("deep.zip")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), names)


class ErrorTests(VfsTestCase):
    """Archives that must be rejected with a readable message."""

    def assert_rejected(self, path: str, text: str) -> None:
        """Expect a VfsError that mentions the given text."""
        with self.assertRaises(VfsError) as context:
            load_vfs(path, "x")
        self.assertIn(text, str(context.exception))

    def test_missing_file(self) -> None:
        """A path that does not exist."""
        self.assert_rejected(str(self.dir / "none.zip"), "file not found")

    def test_directory(self) -> None:
        """A directory instead of a file."""
        self.assert_rejected(str(self.dir), "not a file")

    def test_invalid_archives(self) -> None:
        """Text file, truncated archive and bad checksum."""
        for name in ("not_a_zip.zip", "truncated.zip", "corrupt.zip"):
            with self.subTest(name=name):
                self.assert_rejected(
                    str(self.paths[name]), "invalid ZIP archive"
                )

    def test_unsafe_path(self) -> None:
        """A member that escapes the root."""
        self.assert_rejected(str(self.paths["unsafe.zip"]), "unsafe path")

    def test_clash(self) -> None:
        """A name used as both file and directory."""
        self.assert_rejected(str(self.paths["clash.zip"]), "clash")

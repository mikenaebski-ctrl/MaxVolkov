"""Check command line parameters and their debug description."""

import unittest

from src.config import Config, describe, parse_args


class ConfigTests(unittest.TestCase):
    """Verify parsing of --vfs and --script."""

    def test_defaults(self) -> None:
        """Leave both parameters unset without arguments."""
        config = parse_args([])
        self.assertIsNone(config.vfs_path)
        self.assertIsNone(config.script_path)
        self.assertEqual(config.vfs_name, "demo-vfs")

    def test_both_parameters(self) -> None:
        """Read both paths and name the VFS after its file."""
        config = parse_args(["--vfs", "a/b/disk.zip", "--script", "s.txt"])
        self.assertEqual(config.vfs_path, "a/b/disk.zip")
        self.assertEqual(config.script_path, "s.txt")
        self.assertEqual(config.vfs_name, "disk.zip")

    def test_unknown_parameter(self) -> None:
        """Exit with a usage error for an unsupported option."""
        with self.assertRaises(SystemExit):
            parse_args(["--bogus"])

    def test_missing_value(self) -> None:
        """Exit with a usage error when a value is absent."""
        with self.assertRaises(SystemExit):
            parse_args(["--vfs"])

    def test_describe(self) -> None:
        """Print every parameter, including unset ones."""
        lines = describe(Config(vfs_path="x.zip"))
        self.assertEqual(
            lines,
            ["debug: vfs = x.zip", "debug: script = (not set)"],
        )

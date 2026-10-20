"""Check quoting rules independently of the graphical interface."""

import unittest

from src.parser import parse_line


class ParserTests(unittest.TestCase):
    """Verify complete argument values and invalid input."""

    def test_argument_boundaries(self) -> None:
        """Keep spaces, empty values, escapes, and Unicode intact."""
        cases = (
            ('cd "My Documents"', ["cd", "My Documents"]),
            ("ls 'two words'", ["ls", "two words"]),
            ('ls ""', ["ls", ""]),
            (r"ls my\ folder", ["ls", "my folder"]),
            ('ls "a"b', ["ls", "ab"]),
            ('ls "Мои файлы"', ["ls", "Мои файлы"]),
            ("ls first second", ["ls", "first", "second"]),
        )
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), expected)

    def test_empty_input(self) -> None:
        """Ignore a blank line and whitespace."""
        for line in ("", "   ", "\t"):
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), [])

    def test_invalid_quoting(self) -> None:
        """Reject unmatched quotes and an unfinished escape."""
        for line in ('ls "unfinished', "cd 'unfinished", "ls \\"):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_shell_characters_are_literal(self) -> None:
        """Keep a hash as an argument until script support is added."""
        self.assertEqual(parse_line("ls #"), ["ls", "#"])

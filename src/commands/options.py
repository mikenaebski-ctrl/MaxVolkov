"""Parse UNIX-style short options shared by the commands."""

from dataclasses import dataclass
from typing import Dict, List, Set

from ..errors import CommandError

END_OF_OPTIONS = "--"
OPTION_PREFIX = "-"


@dataclass(frozen=True)
class OptionSpec:
    """Name the accepted flag letters and letters that take a value."""

    flags: str = ""
    valued: str = ""


@dataclass(frozen=True)
class Options:
    """Parsed flags, option values and remaining operands."""

    flags: Set[str]
    values: Dict[str, str]
    operands: List[str]


def read_option(
    command: str,
    spec: OptionSpec,
    argument: str,
    queue: List[str],
    result: Options,
) -> None:
    """Apply one argument such as -al or -L2 to the result."""
    for index, letter in enumerate(argument[len(OPTION_PREFIX):]):
        if letter in spec.flags:
            result.flags.add(letter)
        elif letter in spec.valued:
            rest = argument[len(OPTION_PREFIX) + index + len(letter):]
            if not rest and not queue:
                raise CommandError(
                    f"{command}: option requires an argument -- '{letter}'"
                )
            result.values[letter] = rest or queue.pop(0)
            return
        else:
            raise CommandError(f"{command}: invalid option -- '{letter}'")


def parse_options(
    command: str, arguments: List[str], spec: OptionSpec
) -> Options:
    """Split arguments into options and operands, honoring --."""
    result = Options(set(), {}, [])
    queue = list(arguments)
    while queue:
        argument = queue.pop(0)
        if argument == END_OF_OPTIONS:
            result.operands.extend(queue)
            break
        if argument.startswith(OPTION_PREFIX) and argument != OPTION_PREFIX:
            read_option(command, spec, argument, queue, result)
        else:
            result.operands.append(argument)
    return result

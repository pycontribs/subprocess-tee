"""Module that helps integrating with rich library."""
import io
import sys
from typing import IO, Any, List

from rich.console import Console


# Base on private utility class from
# https://github.com/willmcgugan/rich/blob/master/rich/progress.py#L476
class FileProxy(io.TextIOBase):
    """Wraps a file (e.g. sys.stdout) and redirects writes to a console."""

    def __init__(self, console: Console, file: IO[str]) -> None:
        super().__init__()
        self.__console = console
        self.__file = file
        self.__buffer: List[str] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__file, name)

    def write(self, text: str) -> int:
        buffer = self.__buffer
        lines: List[str] = []
        while text:
            line, new_line, text = text.partition("\n")
            if new_line:
                lines.append("".join(buffer) + line)
                del buffer[:]
            else:
                buffer.append(line)
                break
        if lines:
            console = self.__console
            with console:
                output = "\n".join(lines)
                console.print(output, markup=False, emoji=False, highlight=False)
        return len(text)

    def flush(self) -> None:
        buffer = self.__buffer
        if buffer:
            self.__console.print("".join(buffer))
            del buffer[:]


class ConsoleEx(Console):
    """Extends rich Console class."""

    def __init__(self, *args, **kwargs):
        self.redirect = kwargs.get("redirect", False)
        if "redirect" in kwargs:
            del kwargs["redirect"]
        super().__init__(*args, **kwargs)
        self.extended = True
        if self.redirect:
            sys.stdout = FileProxy(self, sys.stdout)
            sys.stderr = FileProxy(self, sys.stderr)

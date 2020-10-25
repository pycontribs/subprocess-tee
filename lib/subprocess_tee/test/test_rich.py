"""Tests for rich module."""
import sys

from subprocess_tee import run
from subprocess_tee.rich import ConsoleEx


def test_rich_console_ex():
    """Validate that ConsoleEx can capture output from print() calls."""
    console = ConsoleEx(record=True, redirect=True)
    console.print("alpha")
    print("beta")
    sys.stdout.write("gamma\n")
    sys.stderr.write("delta\n")
    proc = run("echo 123")
    assert proc.stdout == "123\n"
    text = console.export_text()
    assert text == "alpha\nbeta\ngamma\ndelta\n123\n"

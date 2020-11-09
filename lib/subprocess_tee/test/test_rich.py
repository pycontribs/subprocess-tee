"""Tests for rich module."""
import sys

from subprocess_tee import run
from subprocess_tee.rich import ConsoleEx


def test_rich_console_ex() -> None:
    """Validate that ConsoleEx can capture output from print() calls."""
    console = ConsoleEx(record=True, redirect=True)
    console.print("alpha")
    print("beta")
    sys.stdout.write("gamma\n")
    sys.stderr.write("delta\n")
    # While not supposed to happen we want to be sure that this will not raise
    # an exception. Some libraries may still sometimes send bytes to the
    # streams, notable example being click.
    sys.stdout.write(b"epsilon\n")  # type: ignore
    proc = run("echo 123")
    assert proc.stdout == "123\n"
    text = console.export_text()
    assert text == "alpha\nbeta\ngamma\ndelta\nepsilon\n123\n"


def test_rich_console_ex_ansi() -> None:
    """Validate that ANSI sent to sys.stdout does not become garbage in record."""
    print()
    console = ConsoleEx(force_terminal=True, record=True, redirect=True)
    console.print("[green]this from Console.print()[/green]", style="red")
    proc = run(r'echo -e "\033[31mred\033[0m"')
    assert proc.returncode == 0
    assert "\x1b[31mred\x1b[0m\n" in proc.stdout

    # validate that what rich recorded is the same as what the subprocess produced
    text = console.export_text(clear=False)
    assert "\x1b[31mred\x1b[0m\n" in text

    # validate that html export also contains at least the "red" text
    html = console.export_html(clear=False)
    assert "red" in html

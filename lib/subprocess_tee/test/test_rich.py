"""Tests for rich module."""
import sys

from enrich.console import Console

from subprocess_tee import run


def test_rich_console_ex() -> None:
    """Validate that ConsoleEx can capture output from print() calls."""
    console = Console(record=True, redirect=True)
    console.print("alpha")
    print("beta")
    sys.stdout.write("gamma\n")
    sys.stderr.write("delta\n")
    # While not supposed to happen we want to be sure that this will not raise
    # an exception. Some libraries may still sometimes send bytes to the
    # streams, notable example being click.
    # sys.stdout.write(b"epsilon\n")  # type: ignore
    proc = run("echo 123")
    assert proc.stdout == "123\n"
    text = console.export_text()
    assert text == "alpha\nbeta\ngamma\ndelta\n123\n"


def test_rich_console_ex_ansi() -> None:
    """Validate that ANSI sent to sys.stdout does not become garbage in record."""
    print()
    console = Console(force_terminal=True, record=True, redirect=True)
    console.print("[green]this from Console.print()[/green]", style="red")
    proc = run(r'echo -e "\033[31mred\033[0m"')
    assert proc.returncode == 0
    assert "red" in proc.stdout

    # validate that what rich recorded is the same as what the subprocess produced
    text = console.export_text(clear=False)
    assert "red" in text

    # validate that html export also contains at least the "red" text
    html = console.export_html(clear=False)
    assert '<span class="r3">red</span>' in html

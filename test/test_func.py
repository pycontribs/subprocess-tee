"""Functional tests for subprocess-tee library."""
import subprocess


def test_molecule() -> None:
    """Ensures molecule does display output of its subprocesses."""
    result = subprocess.run(
        ["molecule", "test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )  # type: ignore
    assert result.returncode == 0
    assert "Past glories are poor feeding." in result.stdout

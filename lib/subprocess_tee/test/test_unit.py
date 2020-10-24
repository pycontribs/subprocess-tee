"""Unittests."""
import subprocess
from subprocess_tee import run


def test_1():
    """One test."""
    cmd = "echo 111 && >&2 echo 222"
    old_result = subprocess.run(
        cmd,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    result = run(cmd)
    assert result.returncode == old_result.returncode
    assert result.stdout == old_result.stdout
    assert result.stderr == old_result.stderr


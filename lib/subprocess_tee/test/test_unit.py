"""Unittests."""
import subprocess

from subprocess_tee import run


def test_run_string():
    """Valida run() called with a single string command."""
    cmd = "echo 111 && >&2 echo 222"
    old_result = subprocess.run(
        cmd,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = run(cmd)
    assert result.returncode == old_result.returncode
    assert result.stdout == old_result.stdout
    assert result.stderr == old_result.stderr


def test_run_list():
    """Validate run call with a command made of list of strings."""
    # NOTICE: subprocess.run() does fail to capture any output when cmd is
    # a list and you specific shell=True. Still, when not mentioning shell,
    # it does work.
    cmd = ["python", "--version"]
    old_result = subprocess.run(
        cmd,
        # shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = run(cmd)
    assert result.returncode == old_result.returncode
    assert result.stdout == old_result.stdout
    assert result.stderr == old_result.stderr

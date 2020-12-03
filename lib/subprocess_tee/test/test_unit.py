"""Unittests."""
import subprocess
from typing import Dict

import pytest
from _pytest.capture import CaptureFixture

from subprocess_tee import run


def test_run_string() -> None:
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


def test_run_list() -> None:
    """Validate run call with a command made of list of strings."""
    # NOTICE: subprocess.run() does fail to capture any output when cmd is
    # a list and you specific shell=True. Still, when not mentioning shell,
    # it does work.
    cmd = ["python3", "--version"]
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


def test_run_echo(capsys: CaptureFixture[str]) -> None:
    """Validate run call with echo dumps command."""
    cmd = ["python3", "--version"]
    old_result = subprocess.run(
        cmd,
        # shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = run(cmd, echo=True)
    assert result.returncode == old_result.returncode
    assert result.stdout == old_result.stdout
    assert result.stderr == old_result.stderr
    out, err = capsys.readouterr()
    assert out.startswith("COMMAND:")
    assert err == ""


@pytest.mark.parametrize(
    "env",
    [{}, {"SHELL": "/bin/sh"}, {"SHELL": "/bin/bash"}, {"SHELL": "/bin/zsh"}],
    ids=["auto", "sh", "bash", "zsh"],
)
def test_run_with_env(env: Dict[str, str]) -> None:
    """Validate that passing custom env to run() works."""
    env["FOO"] = "BAR"
    result = run("echo $FOO", env=env, echo=True)
    assert result.stdout == "BAR\n"


def test_run_shell() -> None:
    """Validate run call with multiple shell commands works."""
    cmd = "echo a && echo b && false || exit 4"
    # "python --version"
    result = run(cmd, echo=True)
    assert result.returncode == 4
    assert result.stdout == "a\nb\n"


def test_run_shell_undefined() -> None:
    """Validate run call with multiple shell commands works."""
    cmd = "echo a && echo b && false || exit 4"
    # "python --version"
    result = run(cmd, echo=True, env={})
    assert result.returncode == 4
    assert result.stdout == "a\nb\n"


def test_run_cwd() -> None:
    """Validate that run accepts cwd and respects it."""
    cmd = "pwd"
    result = run(cmd, echo=True, cwd="/")
    assert result.returncode == 0
    assert result.stdout == "/\n"

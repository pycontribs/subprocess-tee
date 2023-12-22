"""Unittests."""
import subprocess
import sys
from typing import Dict

import pytest
from _pytest.capture import CaptureFixture

from subprocess_tee import run

FAILING_CMD = "echo stdout && echo stderr >&2 && exit 42"
SUCCEEDING_CMD = "echo stdout && echo stderr >&2"


def test_run_string() -> None:
    """Valida run() called with a single string command."""
    cmd = "echo 111 && echo 222 >&2"
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
    cmd = [sys.executable, "--version"]
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
    cmd = [sys.executable, "--version"]
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


def test_run_with_check_raise() -> None:
    """Asure compatibility with subprocess.run when using check (return 1)."""
    with pytest.raises(subprocess.CalledProcessError) as ours:
        run(FAILING_CMD, check=True, shell=True)
    with pytest.raises(subprocess.CalledProcessError) as original:
        subprocess.run(
            FAILING_CMD,
            check=True,
            universal_newlines=True,
            shell=True,
            capture_output=True,
        )
    assert ours.value.cmd == original.value.cmd
    _check_failed_run(ours.value)
    _check_failed_run(original.value)


@pytest.mark.parametrize("check", [True, False])
def test_run_with_check_pass(check) -> None:
    """Asure compatibility with subprocess.run when using check (return 0)."""
    ours = run("true", check=check)
    original = subprocess.run(
        "true", check=check, universal_newlines=True, capture_output=True
    )
    assert ours.returncode == original.returncode
    assert ours.args == original.args
    assert ours.stdout == original.stdout
    assert ours.stderr == original.stderr


def test_run_compat() -> None:
    """Assure compatiblity with subprocess.run()."""
    ours = run(SUCCEEDING_CMD)
    original = subprocess.run(
        SUCCEEDING_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
        shell=True,
    )
    assert ours.args == original.args
    _check_succeeded_run(ours)
    _check_succeeded_run(original)


def _check_succeeded_run(completed_process):
    assert completed_process.returncode == 0
    assert completed_process.stdout == "stdout\n"
    assert completed_process.stderr == "stderr\n"


def _check_failed_run(completed_process):
    assert completed_process.returncode == 42
    assert completed_process.output == "stdout\n"
    assert completed_process.stdout == "stdout\n"
    assert completed_process.stderr == "stderr\n"

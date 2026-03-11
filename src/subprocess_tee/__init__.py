"""tee like run implementation."""

# cspell: ignore popenargs preexec startupinfo creationflags pipesize

from __future__ import annotations

import asyncio
import logging
import os
import platform
import subprocess  # noqa: S404
import sys
from asyncio import StreamReader
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from shlex import join
from typing import TYPE_CHECKING, Any

try:
    __version__ = version("subprocess-tee")
except PackageNotFoundError:  # pragma: no branch
    __version__ = "0.1.dev1"

__all__ = ["CompletedProcess", "__version__", "run"]
_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from subprocess_tee._types import StrOrBytesPath
CompletedProcess = subprocess.CompletedProcess

STREAM_LIMIT = 2**23  # 8MB instead of default 64kb, override it if you need


async def _read_stream(stream: StreamReader, callback: Callable[..., Any]) -> None:
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break


# pylint: disable=too-many-arguments, too-many-locals
async def _stream_subprocess(  # noqa: C901
    args: StrOrBytesPath | Sequence[StrOrBytesPath],
    *,
    stdin=None,
    tee=True,
    quiet=False,
    check=False,
    executable=None,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    platform_settings: dict[str, Any] = {}
    if platform.system() == "Windows":
        platform_settings["env"] = os.environ

    # pop arguments so that we can ensure there are no unexpected arguments
    stdout = kwargs.pop("stdout", sys.stdout)
    stderr = kwargs.pop("stderr", sys.stderr)
    for arg in ["cwd", "env"]:
        if arg in kwargs:
            platform_settings[arg] = kwargs.pop(arg)
    if kwargs:
        msg = f"Popen.__init__() got an unexpected keyword argument '{next(iter(kwargs.keys()))}'"
        raise TypeError(msg)
    del kwargs

    with Path(os.devnull).open("w", encoding="UTF-8") as devnull:
        if stdout == subprocess.DEVNULL or not tee:
            stdout = devnull
        if stderr == subprocess.DEVNULL or not tee:
            stderr = devnull

        # We need to tell subprocess which shell to use when running shell-like
        # commands.
        # * SHELL is not always defined
        # * /bin/bash does not exit on alpine, /bin/sh seems bit more portable
        if executable is None and isinstance(args, str) and " " in args:
            executable = os.environ.get("SHELL", "/bin/sh")

        if isinstance(args, os.PathLike):
            args = os.fspath(args)
        # Some users are reporting that default (undocumented) limit 64k is too
        # low
        if isinstance(args, (str, bytes)):
            process = await asyncio.create_subprocess_shell(
                args,
                limit=STREAM_LIMIT,
                stdin=stdin,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                executable=executable,
                **platform_settings,
            )
        else:
            process = await asyncio.create_subprocess_exec(
                *args,
                limit=STREAM_LIMIT,
                stdin=stdin,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                executable=executable,
                **platform_settings,
            )
        out: list[str] = []
        err: list[str] = []

        def tee_func(line: bytes, sink: list[str], pipe: Any | None) -> None:
            line_str = line.decode("utf-8").rstrip()
            sink.append(line_str)
            if not quiet:
                if pipe and hasattr(pipe, "write"):
                    print(line_str, file=pipe)
                else:
                    print(line_str)  # noqa: T201

        loop = asyncio.get_running_loop()
        tasks = []
        if process.stdout:
            tasks.append(
                loop.create_task(
                    _read_stream(process.stdout, lambda x: tee_func(x, out, stdout)),
                ),
            )
        if process.stderr:
            tasks.append(
                loop.create_task(
                    _read_stream(process.stderr, lambda x: tee_func(x, err, stderr)),
                ),
            )

        await asyncio.wait(set(tasks))

        # We need to be sure we keep the stdout/stderr output identical with
        # the ones produced by subprocess.run(), at least when in text mode.
        stdout = None if check else ""
        stderr = None if check else ""
        if out:
            stdout = os.linesep.join(out) + os.linesep
        if err:
            stderr = os.linesep.join(err) + os.linesep

        return subprocess.CompletedProcess(
            args=args,
            returncode=await process.wait(),
            stdout=stdout,
            stderr=stderr,
        )


# signature is based on stdlib
# subprocess.run()
# pylint: disable=too-many-arguments
# ruff: ignore=FBT001,ARG001
def run(
    args: StrOrBytesPath | Sequence[StrOrBytesPath] | None = None,
    bufsize: int = -1,
    input: bytes | str | None = None,  # noqa: A002
    *,
    capture_output: bool = True,
    timeout: int | None = None,
    check: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Drop-in replacement for subprocess.run that behaves like tee.

    Not all arguments to subprocess.run are supported.

    Extra arguments added by our version:
    echo: False - Prints command before executing it.
    quiet: False - Avoid printing output

    Returns:
        CompletedProcess: ...

    Raises:
        CalledProcessError: ...
        TypeError: ...

    """
    if args is None:
        msg = "Popen.__init__() missing 1 required positional argument: 'args'"
        raise TypeError(msg)

    # bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None, close_fds=True, shell=False, cwd=None, env=None, universal_newlines=None, startupinfo=None, creationflags=0, restore_signals=True, start_new_session=False, pass_fds=(), *, group=None, extra_groups=None, user=None, umask=-1, encoding=None, errors=None, text=None, pipesize=-1, process_group=None
    if bufsize != -1:
        msg = f"Ignored bufsize argument as it is not supported yet by {__package__}"
        _logger.warning(msg)
    if input is not None:
        msg = f"Ignored input argument as it is not supported yet by {__package__}"
        _logger.warning(msg)
    if timeout is not None:
        msg = f"Ignored timeout argument as it is not supported yet by {__package__}"
        _logger.warning(msg)
    if not capture_output:
        msg = f"Ignored capture_output argument as it is not supported yet by {__package__}"
        _logger.warning(msg)
    kwargs["check"] = check

    check = kwargs.get("check", False)

    if kwargs.pop("echo", False):
        cmd = (
            args
            if isinstance(args, (str, bytes, os.PathLike))
            else join(str(s) for s in args)
        )
        print(f"COMMAND: {cmd}")  # noqa: T201

    result = asyncio.run(_stream_subprocess(args, **kwargs))
    # we restore original args to mimic subprocess.run()
    result.args = args

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            args,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result

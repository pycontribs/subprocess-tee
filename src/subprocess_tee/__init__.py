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
    from subprocess_tee._types import SequenceNotStr

    CompletedProcess = subprocess.CompletedProcess[Any]
    from collections.abc import Callable
else:
    CompletedProcess = subprocess.CompletedProcess

STREAM_LIMIT = 2**23  # 8MB instead of default 64kb, override it if you need


async def _read_stream(stream: StreamReader, callback: Callable[..., Any]) -> None:
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break


async def _stream_subprocess(  # noqa: C901
    args: str | tuple[str, ...],
    **kwargs: Any,
) -> CompletedProcess:
    platform_settings: dict[str, Any] = {}
    if platform.system() == "Windows":
        platform_settings["env"] = os.environ

    # this part keeps behavior backwards compatible with subprocess.run
    tee = kwargs.get("tee", True)
    stdout = kwargs.get("stdout", sys.stdout)

    with Path(os.devnull).open("w", encoding="UTF-8") as devnull:
        if stdout == subprocess.DEVNULL or not tee:
            stdout = devnull
        stderr = kwargs.get("stderr", sys.stderr)
        if stderr == subprocess.DEVNULL or not tee:
            stderr = devnull

        # We need to tell subprocess which shell to use when running shell-like
        # commands.
        # * SHELL is not always defined
        # * /bin/bash does not exit on alpine, /bin/sh seems bit more portable
        if "executable" not in kwargs and isinstance(args, str) and " " in args:
            platform_settings["executable"] = os.environ.get("SHELL", "/bin/sh")

        # pass kwargs we know to be supported
        for arg in ["cwd", "env"]:
            if arg in kwargs:
                platform_settings[arg] = kwargs[arg]

        # Some users are reporting that default (undocumented) limit 64k is too
        # low
        if isinstance(args, str):
            process = await asyncio.create_subprocess_shell(
                args,
                limit=STREAM_LIMIT,
                stdin=kwargs.get("stdin", False),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **platform_settings,
            )
        else:
            process = await asyncio.create_subprocess_exec(
                *args,
                limit=STREAM_LIMIT,
                stdin=kwargs.get("stdin", False),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **platform_settings,
            )
        out: list[str] = []
        err: list[str] = []

        def tee_func(line: bytes, sink: list[str], pipe: Any | None) -> None:
            line_str = line.decode("utf-8").rstrip()
            sink.append(line_str)
            if not kwargs.get("quiet"):
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
        check = kwargs.get("check", False)
        stdout = None if check else ""
        stderr = None if check else ""
        if out:
            stdout = os.linesep.join(out) + os.linesep
        if err:
            stderr = os.linesep.join(err) + os.linesep

        return CompletedProcess(
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
    args: str | SequenceNotStr[str] | None = None,
    bufsize: int = -1,
    input: bytes | str | None = None,  # noqa: A002
    *,
    capture_output: bool = False,
    timeout: int | None = None,
    check: bool = False,
    **kwargs: Any,
) -> CompletedProcess:
    """Drop-in replacement for subprocess.run that behaves like tee.

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

    cmd = args if isinstance(args, str) else join(args)
    # bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None, close_fds=True, shell=False, cwd=None, env=None, universal_newlines=None, startupinfo=None, creationflags=0, restore_signals=True, start_new_session=False, pass_fds=(), *, group=None, extra_groups=None, user=None, umask=-1, encoding=None, errors=None, text=None, pipesize=-1, process_group=None
    if bufsize != -1:
        msg = "Ignored bufsize argument as it is not supported yet by __package__"
        _logger.warning(msg)
    kwargs["check"] = check
    kwargs["input"] = input
    kwargs["timeout"] = timeout
    kwargs["capture_output"] = capture_output

    check = kwargs.get("check", False)

    if kwargs.get("echo"):
        print(f"COMMAND: {cmd}")  # noqa: T201

    result = asyncio.run(_stream_subprocess(cmd, **kwargs))
    # we restore original args to mimic subprocess.run()
    result.args = args

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,  # pyright: ignore[xxx]
            output=result.stdout,
            stderr=result.stderr,
        )
    return result

"""tee like run implementation."""
import asyncio
import os
import platform
import subprocess
import sys
from asyncio import StreamReader
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

if TYPE_CHECKING:
    CompletedProcess = subprocess.CompletedProcess[Any]  # pylint: disable=E1136
else:
    CompletedProcess = subprocess.CompletedProcess

try:
    from shlex import join  # type: ignore
except ImportError:
    from subprocess import list2cmdline as join  # pylint: disable=ungrouped-imports


async def _read_stream(stream: StreamReader, callback: Callable[..., Any]) -> None:
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break


async def _stream_subprocess(args: str, **kwargs: Any) -> CompletedProcess:
    platform_settings: Dict[str, Any] = {}
    if platform.system() == "Windows":
        platform_settings["env"] = os.environ

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

    process = await asyncio.create_subprocess_shell(
        args,
        stdin=kwargs.get("stdin", False),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **platform_settings,
    )
    out: List[str] = []
    err: List[str] = []

    def tee(line: bytes, sink: List[str], pipe: Optional[Any]) -> None:
        line_str = line.decode("utf-8").rstrip()
        sink.append(line_str)
        if not kwargs.get("quiet", False):
            print(line_str, file=pipe)

    loop = asyncio.get_event_loop()
    tasks = []
    if process.stdout:
        tasks.append(
            loop.create_task(
                _read_stream(process.stdout, lambda l: tee(l, out, sys.stdout))
            )
        )
    if process.stderr:
        tasks.append(
            loop.create_task(
                _read_stream(process.stderr, lambda l: tee(l, err, sys.stderr))
            )
        )

    await asyncio.wait(set(tasks))

    # We need to be sure we keep the stdout/stderr output identical with
    # the ones procued by subprocess.run(), at least when in text mode.
    return CompletedProcess(
        args=args,
        returncode=await process.wait(),
        stdout=os.linesep.join(out) + os.linesep,
        stderr=(os.linesep.join(err) + os.linesep) if err else "",
    )


def run(args: Union[str, List[str]], **kwargs: Any) -> CompletedProcess:
    """Drop-in replacement for subprocerss.run that behaves like tee.

    Extra arguments added by our version:
    echo: False - Prints command before executing it.
    quiet: False - Avoid printing output
    """
    if isinstance(args, str):
        cmd = args
    else:
        # run was called with a list instead of a single item but asyncio
        # create_subprocess_shell requires command as a single string, so
        # we need to convert it to string
        cmd = join(args)

    if kwargs.get("echo", False):
        print(f"COMMAND: {cmd}")

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_stream_subprocess(cmd, **kwargs))
    return result

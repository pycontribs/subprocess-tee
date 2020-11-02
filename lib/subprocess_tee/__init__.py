"""tee-like run implementation."""
import asyncio
import os
import platform
import sys
from subprocess import CompletedProcess
from typing import Any, Callable, Dict, List, Optional

try:
    from shlex import join  # type: ignore
except ImportError:
    from subprocess import list2cmdline as join  # pylint: disable=ungrouped-imports


async def _read_stream(stream, callback: Callable):
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break


async def _stream_subprocess(args, **kwargs) -> CompletedProcess:
    platform_settings: Dict[str, Any] = {}
    if platform.system() == "Windows":
        platform_settings["env"] = os.environ

    # We need to tell subprocess which shell to use when running shell-like
    # commands.
    # * SHELL is not always defined
    # * /bin/bash does not exit on alpine, /bin/sh seems bit more portable
    if "executable" not in kwargs and isinstance(args, str) and " " in args:
        platform_settings["executable"] = os.environ.get("SHELL", "/bin/sh")

    if "env" in kwargs:
        platform_settings["env"] = kwargs["env"]

    process = await asyncio.create_subprocess_shell(
        args,
        stdin=kwargs.get("stdin", False),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **platform_settings,
    )
    out: List[str] = []
    err: List[str] = []

    def tee(line: bytes, sink: List[str], pipe: Optional[Any]):
        line_str = line.decode("utf-8").rstrip()
        sink.append(line_str)
        if not kwargs.get("quiet", False):
            print(line_str, file=pipe)

    loop = asyncio.get_event_loop()
    task1 = loop.create_task(
        _read_stream(process.stdout, lambda l: tee(l, out, sys.stdout))
    )
    task2 = loop.create_task(
        _read_stream(process.stderr, lambda l: tee(l, err, sys.stderr))
    )

    await asyncio.wait({task1, task2})

    # We need to be sure we keep the stdout/stderr output identical with
    # the ones procued by subprocess.run(), at least when in text mode.
    return CompletedProcess(
        args=args,
        returncode=await process.wait(),
        stdout=os.linesep.join(out) + os.linesep,
        stderr=(os.linesep.join(err) + os.linesep) if err else "",
    )


def run(cmd, **kwargs):
    """Drop-in replacement for subprocerss.run that behaves like tee.

    Extra arguments added by our version:
    echo: False - Prints command before executing it.
    quiet: False - Avoid printing output
    """
    if not isinstance(cmd, str):
        # run was called with a list instead of a single item but asyncio
        # create_subprocess_shell requires command as a single string, so
        # we need to convert it to string
        cmd = join(cmd)

    if not isinstance(cmd, str):
        raise RuntimeError(f"Unable to process {cmd}")

    if kwargs.get("echo", False):
        print(f"COMMAND: {cmd}")

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_stream_subprocess(cmd, **kwargs))
    return result

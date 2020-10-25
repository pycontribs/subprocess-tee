"""tee-like run implementation."""
import asyncio
import os
import platform
import sys
from subprocess import CompletedProcess
from typing import Any, Callable, Dict, List, Optional


async def _read_stream(stream, callback: Callable):
    while True:
        line = await stream.readline()
        if line:
            callback(line)
        else:
            break


async def _stream_subprocess(args, **kwargs) -> CompletedProcess:
    if platform.system() == "Windows":
        platform_settings: Dict[str, Any] = {"env": os.environ}
    else:
        platform_settings = {"executable": "/bin/bash"}

    if kwargs.get("echo", False):
        print(*args)

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

    return CompletedProcess(
        args=args,
        returncode=await process.wait(),
        stdout=os.linesep.join(out) + os.linesep,
        stderr=os.linesep.join(err) + os.linesep,
    )


def run(*args, **kwargs):
    """Drop-in replacement for subprocerss.run that behaves like tee.

    Extra arguments added by our version:
    echo: False - Prints command before executing it.
    quiet: False - Avoid printing output
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_stream_subprocess(*args, **kwargs))
    return result

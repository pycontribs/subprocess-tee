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


async def _stream_subprocess(
    cmd, stdin=None, quiet=False, echo=False
) -> CompletedProcess:
    if platform.system() == "Windows":
        platform_settings: Dict[str, Any] = {"env": os.environ}
    else:
        platform_settings = {"executable": "/bin/bash"}

    if echo:
        print(cmd)

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdin=stdin,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **platform_settings
    )
    out: List[str] = []
    err: List[str] = []

    def tee(line: bytes, sink: List[str], pipe: Optional[Any]):
        line_str = line.decode("utf-8").rstrip()
        sink.append(line_str)
        if not quiet:
            print(line, file=pipe)

    await asyncio.wait(
        set(
            [
                _read_stream(process.stdout, lambda l: tee(l, out, sys.stdout)),
                _read_stream(process.stderr, lambda l: tee(l, err, sys.stderr)),
            ]
        )
    )

    return CompletedProcess(
        args=cmd,
        returncode=await process.wait(),
        stdout=os.linesep.join(out) + os.linesep,
        stderr=os.linesep.join(err) + os.linesep,
    )


def run(cmd, stdin=None, quiet=False, echo=False) -> CompletedProcess:
    """Drop-in replacement for subprocerss.run that does tee."""
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        _stream_subprocess(cmd, stdin=stdin, quiet=quiet, echo=echo)
    )

    return result

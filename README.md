# subprocess-tee

This package provides a drop-in alternative to `subprocess.run` that
captures the output while still printing it in **real-time**, just the way
`tee` does.

Printing output in real-time while still capturing is valuable for
any tool that executes long-running child processes. For those, you do want
to provide instant feedback (progress) related to what is happening.

```python
# from subprocess import run
from subprocess_tee import run

result = run("echo 123")
result.stdout == "123\n"
```

You can add `tee=False` to disable the tee functionality if you want, this
being a much shorter alternative than adding the well known
`stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL`.

Keep in mind that `universal_newlines=True` is implied as we expect text
processing, this being a divergence from the original `subprocess.run`.

You can still use `check=True` in order to make it raise CompletedProcess
exception when the result code is not zero.

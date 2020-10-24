# subprocess-tee

This package provides an drop-in alternative to `subprocess.run` that
captures the output while still printing it in **real time**, just the way `tee` does.

Printing output in real-time while still capturing is important for
any tool that executes long running child processes, as you may not want
to deprive user from getting instant feedback related to what is happening.

```python
# from subprocess import run
from subprocess_tee import run

result = run("echo 123")
result.stdout == "123\n"
```

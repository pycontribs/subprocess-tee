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

## Rich extension

This libary also provides an drop-in replacement for rich Console class, one
that is able to rewire both `sys.stdout` and `sys.stderr` and avoid the
need too replace bare `print()` calls with `console.print()` ones.

```python
# from rich.console import Console
from subprocess_tee.rich import ConsoleEx

console = ConsoleEx(redirect=True, record=True)
print("123")
assert "123\n" == console.export_text()
```

When used in conjuction with our own `run()`, this also makes it possible
to use rich to process output produced by subprocesses.

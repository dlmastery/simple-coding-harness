# 00b-environment-metadata

Executable: C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\simple-coding-harness\.venv\Scripts\python.exe

Arguments:

- -c
- import importlib.metadata as m; print("
".join(sorted(d.metadata["Name"]+"=="+d.version for d in m.distributions())))

Exit: 1; signal: null; wall seconds: 0.0485972.

```text
  File "<string>", line 1
    import importlib.metadata as m; print("
                                          ^
SyntaxError: unterminated string literal (detected at line 1)

```

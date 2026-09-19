"""Stage 15 - the input line.

`input()` cannot edit a line that has wrapped past the screen width - the
terminal owns the wrapping and readline cannot see it. prompt_toolkit redraws
the line itself, so deleting, word jumps and history all keep working once
the text is longer than the screen. It also gives persistent history and
alt-enter for a newline.
"""

import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from . import config

HISTORY = config.HOME / "history"
STYLE = Style.from_dict({"prompt": "bold #9ece6a"})

bindings = KeyBindings()


@bindings.add("escape", "enter")
def _newline(event):
    """alt/option-enter starts a new line instead of sending the message."""
    event.current_buffer.insert_text("\n")


SESSION = None


def read(prompt="> "):
    """Read one message. Raises EOFError on ctrl-d, like input() does.

    Without a real terminal (piped stdin, a plain Windows pipe, tests) the
    editor cannot start, so fall back to input() rather than refuse to run.
    """
    global SESSION
    if not sys.stdin.isatty():
        return plain(prompt)
    if SESSION is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        try:
            SESSION = PromptSession(history=FileHistory(str(HISTORY)), key_bindings=bindings, style=STYLE)
        except Exception:  # noqa: BLE001 - e.g. NoConsoleScreenBufferError on Windows
            SESSION = False
    if not SESSION:
        return plain(prompt)
    return SESSION.prompt(HTML(f"<prompt>{prompt}</prompt>"))


def plain(prompt):
    """input() with the prompt on stderr: in -p mode stdout carries only the answer."""
    sys.stderr.write(prompt)
    sys.stderr.flush()
    return input()

"""The input line.

`input()` cannot edit a line that has wrapped past the screen width - the
terminal owns the wrapping. prompt_toolkit redraws the line itself, so
deleting, word jumps and history keep working on long messages. It also
gives us persistent history across sessions and multi-line input for free.
"""

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
    """alt/option-enter inserts a newline instead of sending."""
    event.current_buffer.insert_text("\n")


_session = None


def read(prompt="> "):
    """Read one message. Raises EOFError on ctrl-d, like input() does."""
    global _session
    if _session is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        _session = PromptSession(history=FileHistory(str(HISTORY)), key_bindings=bindings, style=STYLE)
    return _session.prompt(HTML(f"<prompt>{prompt}</prompt>"))

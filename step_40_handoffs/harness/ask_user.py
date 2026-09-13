"""Step 35 - the ask_user tool. The model puts a question to the user and
the answer comes back as the tool result. The question and its numbered
options are printed by ui.question, and the answer is read with the same
prompt.read the input line uses. A number picks an option; any other text
is the answer as typed. The tool is always allowed, in plan mode too: a
question changes nothing on disk.
"""

from . import prompt

ASK_USER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "ask_user",
        "description": (
            "Ask the user one question and wait for the answer. Use it when a "
            "requirement is ambiguous or a choice cannot be undone. Give options "
            "when there are a few clear ones; the user may also type free text."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question, one sentence"},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Short answers to choose from, in the order to show them",
                },
            },
            "required": ["question"],
        },
    },
}

NO_ANSWER = "(the user gave no answer)"


def ask_user(question: str, options=None) -> str:
    """Print the question and its options, read one line, and return the answer.

    A number from 1 to the number of options returns that option's text.
    Anything else is returned as typed. Ctrl-D or Ctrl-C at the prompt is
    NO_ANSWER, so the model learns the question was not answered.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    options = list(options or [])
    ui.question(question, options)
    try:
        answer = prompt.read("  answer> ").strip()
    except (EOFError, KeyboardInterrupt):
        return NO_ANSWER
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer or NO_ANSWER

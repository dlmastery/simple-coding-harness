"""Step 23 - the browser subagent.

browse(task) is a second subagent, built like subagent.task: a fresh
history, a smaller tool set, the same loop, one report back. Its tools are
the six browser_* tools and read_file. The main agent is offered browse and
nothing else from the browser, so a page dump lands in the subagent's
context and only a short report reaches the main one.
"""

MAX_TURNS = 20  # a page visit takes more steps than a grep

TOOLS = {
    "browser_open",
    "browser_click",
    "browser_type",
    "browser_read",
    "browser_screenshot",
    "browser_close",
    "read_file",
}

SYSTEM_PROMPT = """
You are a browser subagent. A lead agent gave you one task that needs a web
page, and you carry it out. You cannot see the lead agent's conversation, and
it cannot see what you do here. Only your final message crosses back.

How to work:
- browser_open a URL, browser_read to see what is on the page, then
  browser_click or browser_type to move on. Read again after every move.
- Prefer visible text for clicks: the label of the link or button.
- A result that starts with "Error:" is information. Read the page again and
  try another way, or report the block.
- Never enter credentials, payment details, or personal data. If a page asks
  for a login, say so in the report and stop.
- Stop as soon as the task is done. Do not wander.

Your final message is the entire report. Keep it under 200 words: what you
found, the URLs it came from, and anything you could not do.
"""


def toolset():
    """The browser tool schemas plus read_file, nothing else."""
    from .browser import SCHEMAS
    from .tools import TOOL_SCHEMAS

    return [s for s in SCHEMAS + TOOL_SCHEMAS if s["function"]["name"] in TOOLS]


def browse(task: str) -> str:
    """Run a browser subagent on one task and return only its report."""
    from .subagent import loop  # here, not at the top: tools imports us, subagent imports tools

    return loop(SYSTEM_PROMPT, task, toolset(), MAX_TURNS, label="subagent browsing")


BROWSE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "browse",
        "description": (
            "Hand a web task to a browser subagent and get back a short report. "
            "It opens pages, clicks, types and reads in a real browser, in its "
            "own context window, so page contents never enter this "
            "conversation. It cannot see this conversation, so give it the "
            "URL to start from and say exactly what to find or do. It never "
            "enters credentials."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "The task, written to stand alone: the starting URL, "
                        "the steps to take, and what the report should contain."
                    ),
                }
            },
            "required": ["task"],
        },
    },
}

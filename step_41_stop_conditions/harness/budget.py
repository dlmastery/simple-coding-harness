"""Step 32 - the context budget: where the window goes, and when to warn.

Every request the loop sends is the system prompt, the transcript, the late
block and the tool schemas. breakdown() estimates each part in tokens and
sorts the parts into eight categories, so the user can see what fills the
window. render() draws one bar per category. check() returns a warning at
50% and at 75% of the window, once each per session.

The estimate is the one history.estimate uses: four characters to a token,
a picture at a flat rate. The usage line prints it next to the real prompt
count, so a drift is visible instead of hidden.

DEFER_OVER is the line for deferred tools: a schema over this many tokens
is offered as a stub until the model loads it. The stub machinery lives in
tools.py; the measure lives here, next to the other estimates. The line
is 300 tokens, or the DEFER_OVER environment variable.
"""

import json
import os

from . import config
from .history import IMAGE_TOKENS

CATEGORIES = (
    "system prompt",
    "instruction files",
    "skills index",
    "memory index",
    "tool schemas",
    "transcript text",
    "tool results",
    "images",
)

DEFER_OVER = int(os.environ.get("DEFER_OVER", 300))  # tokens; a tool schema over this is deferred
THRESHOLDS = (0.5, 0.75)  # fractions of the window that earn a warning
WARNED = set()            # the thresholds already reported this session
BAR = 30                  # width of the longest bar render() draws


def tokens(text):
    """The estimate for a piece of text."""
    return len(text) // 4


def schema_tokens(schema):
    """The estimate for one tool schema, as the JSON the request carries."""
    return len(json.dumps(schema, separators=(",", ":"))) // 4


def part_of(whole, part):
    """The tokens a part of the system prompt costs, or 0 when it is not in it."""
    return tokens(part) if part and part in whole else 0


def breakdown(messages):
    """Estimated tokens per category for the next request built on messages.

    Returns a dict in CATEGORIES order plus "total" and "window". The system
    prompt is split three ways: the instruction files and the skills index
    are counted on their own, and "system prompt" is what remains. The
    memory index and the tool schemas are not in messages; they ride along
    with every request, so they are counted from their sources.
    """
    # here, not at the top: tools imports llm, and llm imports this module
    from .instructions import instructions_prompt
    from .memory import memory_index
    from .skills import skills_prompt
    from .tools import active_schemas

    system = ""
    rest = messages
    if messages and messages[0].get("role") == "system":
        system = messages[0].get("content") or ""
        rest = messages[1:]
    instructions = part_of(system, instructions_prompt())
    skills = part_of(system, skills_prompt())

    text = results = images = 0
    for message in rest:
        content = message.get("content")
        if isinstance(content, list):
            images += IMAGE_TOKENS * sum(1 for part in content if part.get("type") == "image_url")
            text += sum(tokens(part.get("text", "")) for part in content)
        elif message.get("role") == "tool":
            results += tokens(json.dumps(message))
        else:
            text += tokens(json.dumps(message))

    counts = {
        "system prompt": tokens(system) - instructions - skills,
        "instruction files": instructions,
        "skills index": skills,
        "memory index": tokens(memory_index()),
        "tool schemas": sum(schema_tokens(s) for s in active_schemas()),
        "transcript text": text,
        "tool results": results,
        "images": images,
    }
    counts["total"] = sum(counts.values())
    counts["window"] = config.CONTEXT_WINDOW
    return counts


def render(messages):
    """The breakdown as text: one bar per category, then the share of the window used."""
    counts = breakdown(messages)
    largest = max(counts[category] for category in CATEGORIES) or 1
    lines = []
    for category in CATEGORIES:
        count = counts[category]
        bar = "#" * round(BAR * count / largest)
        lines.append(f"{category:<18} {count:>8,}  {bar}")
    used = 100 * counts["total"] / counts["window"]
    lines.append(f"{'total':<18} {counts['total']:>8,}  {used:.0f}% of the {counts['window']:,} token window")
    return "\n".join(lines)


def check(prompt_tokens):
    """The warning a prompt of this size earns, or None. Each threshold fires once.

    A prompt that jumps past both lines at once earns one warning, for the
    higher line, and both lines count as reported.
    """
    if not prompt_tokens:
        return None
    used = prompt_tokens / config.CONTEXT_WINDOW
    crossed = [t for t in THRESHOLDS if used >= t and t not in WARNED]
    if not crossed:
        return None
    WARNED.update(crossed)
    return (
        f"context window {used:.0%} full: {prompt_tokens:,} of {config.CONTEXT_WINDOW:,} tokens. "
        "/context shows where it goes; /compact frees it"
    )

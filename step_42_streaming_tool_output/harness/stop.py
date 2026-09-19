"""Step 41 - stop conditions: the ways a turn ends on purpose, and the
budgets that end it when the model does not.

finish(summary) is a tool. The model calls it to say the turn is over;
the result is the summary, and the loop stops after the results of that
reply are in, whatever else the reply asked for. The summary is the
answer -p prints.

Three budgets guard a turn that does not end by itself. MAX_TURN_CALLS
is step 34's cap on model calls per turn, moved here. MAX_SESSION_COST
is a cap in dollars on the whole session: every model call is priced,
from the cost the API reported when the usage carries one (OpenRouter
sends it when llm.USAGE_EXTRA asks; other hosts never do) and from PRICES
otherwise - an estimate, and FALLBACK_PRICES for a model not in the
table - and the total is SPENT. MAX_TURN_SECONDS caps the wall-clock
time of one turn. The caps are checked before a model call: a tool that
is already running, a job_wait or a subagent's own calls finish first.
tripped() checks the three before every model call and returns the
report the loop prints when one has been crossed.

A Stop hook (step 27's hooks.json, event "Stop") runs when the turn is
about to end: the model answered without tool calls, or it called
finish. The event carries the answer and every tool call of the turn
with its input and result. A hook that exits 2 blocks the stop: its
stderr becomes a user message, "Stop blocked: ...", and the loop goes on
so the agent reads it and continues. MAX_STOP_BLOCKS blocks in one turn
is the limit, so a hook that is never satisfied cannot keep the agent
running forever.
"""

import json
import os
import sys
import time

from . import hooks


def env_number(name, default):
    """A number from the environment, or the default with a note on stderr when the value is not one."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return type(default)(raw)
    except ValueError:
        print(f"{name}={raw!r} is not a number; using {default}", file=sys.stderr)
        return default


MAX_TURN_CALLS = env_number("MAX_TURN_CALLS", 40)       # model calls one turn may make
MAX_SESSION_COST = env_number("MAX_SESSION_COST", 5.0)  # dollars one session may spend
MAX_TURN_SECONDS = env_number("MAX_TURN_SECONDS", 900.0)  # wall-clock seconds one turn may take
MAX_STOP_BLOCKS = 3      # times the Stop hooks may send the agent back in one turn
RESULT_CHARS = 4000      # how much of each tool result the Stop event carries

clock = time.monotonic   # a name the tests can replace

# dollars per million tokens: prompt, completion, cached prompt. Used when the usage carries no cost.
PRICES = {
    "gpt-4.1-mini": (0.40, 1.60, 0.10),
    "gpt-4.1": (2.00, 8.00, 0.50),
    "gpt-4.1-nano": (0.10, 0.40, 0.025),
}
# a model not in PRICES is priced with these, or with PRICE_PROMPT, PRICE_COMPLETION and PRICE_CACHED from the environment
FALLBACK_PRICES = (
    env_number("PRICE_PROMPT", 1.0),
    env_number("PRICE_COMPLETION", 4.0),
    env_number("PRICE_CACHED", 0.25),
)

SPENT = 0.0       # dollars this session has cost so far, every model call counted
STARTED = None    # clock() when the current turn began
SUMMARY = None    # the summary a finish call gave in this reply, until the loop reads it
BLOCKS = 0        # times the Stop hooks have sent the agent back this turn

FINISH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "finish",
        "description": (
            "End the turn. Call it when the task is done or when nothing more can be "
            "done without the user. The summary is the answer the user reads: what "
            "was done, what was checked, and anything left open."
        ),
        "parameters": {
            "type": "object",
            "properties": {"summary": {"type": "string", "description": "The answer for the user, in a few sentences"}},
            "required": ["summary"],
        },
    },
}


def finish(summary: str) -> str:
    """End the turn after this reply's results are in. Returns the summary."""
    global SUMMARY
    SUMMARY = (str(summary) if summary else "").strip() or "(finished without a summary)"
    return SUMMARY


def finish_summary(arguments):
    """The summary inside the JSON arguments of a finish call, as finish() returned it.

    agent.last_reply accepts it only when the tool's result says the same:
    a finish that a hook blocked or a rule denied did not end the turn.
    """
    try:
        args = json.loads(arguments or "{}")
    except (json.JSONDecodeError, TypeError):
        args = {}
    summary = args.get("summary") if isinstance(args, dict) else None
    return (str(summary) if summary else "").strip() or "(finished without a summary)"


def begin_turn():
    """Start the clock and forget the last turn's finish and blocks."""
    global STARTED, SUMMARY, BLOCKS
    STARTED = clock()
    SUMMARY = None
    BLOCKS = 0


def finished():
    """The summary a finish call gave in this reply, or None. Reading it clears it."""
    global SUMMARY
    summary, SUMMARY = SUMMARY, None
    return summary


def elapsed():
    """Seconds since the turn began; 0 outside a turn."""
    return 0.0 if STARTED is None else clock() - STARTED


# ---------------------------------------------------------------------- cost


def prices():
    """The (prompt, completion, cached) prices of the model in use, per million tokens."""
    from . import llm  # here, not at the top: llm imports tools, tools imports this module

    return PRICES.get(llm.MODEL, FALLBACK_PRICES)


def cost_of(usage):
    """The dollars one model call cost, and where the number came from.

    The cost the usage carries wins: OpenRouter reports one when asked
    (llm.USAGE_EXTRA). Otherwise the tokens are priced from PRICES, with
    the cached part of the prompt at its own rate.
    """
    usage = usage or {}
    if usage.get("cost") is not None:
        return float(usage["cost"]), "reported by the API"
    prompt_price, completion_price, cached_price = prices()
    cached = int(usage.get("cached_tokens") or 0)
    prompt = max(int(usage.get("prompt_tokens") or 0) - cached, 0)
    completion = int(usage.get("completion_tokens") or 0)
    return (prompt * prompt_price + completion * completion_price + cached * cached_price) / 1_000_000, "estimated from list prices"


def record(usage):
    """Add one model call to SPENT. Returns what the call cost."""
    global SPENT
    cost, _ = cost_of(usage)
    SPENT += cost
    return cost


# ------------------------------------------------------------------- budgets


def tripped(calls):
    """The report for the budget this turn has crossed, or None when it may go on.

    calls is how many model calls the turn has made. The three checks run
    before every model call, so the call that would cross a line is the
    one that is not made. A subagent asks with calls=0: the session cost
    and the turn clock bind it too, the call count is its own.
    """
    if calls >= MAX_TURN_CALLS:
        return f"stopped after {calls} model calls in one turn (MAX_TURN_CALLS={MAX_TURN_CALLS}); say continue to go on"
    if SPENT >= MAX_SESSION_COST:
        return (
            f"stopped: this session has cost ${SPENT:.4f}, over MAX_SESSION_COST=${MAX_SESSION_COST:.2f}; "
            "raise it in the environment and start again"
        )
    seconds = elapsed()
    if seconds >= MAX_TURN_SECONDS:
        return f"stopped after {seconds:.0f}s in one turn (MAX_TURN_SECONDS={MAX_TURN_SECONDS:.0f}); say continue to go on"
    return None


def status():
    """One line for /cost: what the session spent, the caps, and the turn's clock."""
    return (
        f"session cost ${SPENT:.4f} of MAX_SESSION_COST=${MAX_SESSION_COST:.2f} ({source()}); "
        f"MAX_TURN_CALLS={MAX_TURN_CALLS}; MAX_TURN_SECONDS={MAX_TURN_SECONDS:.0f}; Stop hook blocks this turn: {BLOCKS}"
    )


def source():
    """Where the session's cost numbers come from, for /cost."""
    from . import llm  # here, not at the top: see prices()

    return "list prices" if llm.MODEL in PRICES else "fallback prices, set PRICE_PROMPT, PRICE_COMPLETION and PRICE_CACHED"


# ------------------------------------------------------------------ the hook


def turn_calls(messages, start):
    """Every tool call the turn made, oldest first, with its input and result.

    start is the length of the transcript before the turn's user message.
    Each entry has the PostToolUse keys - tool_name, tool_input,
    tool_result - so a Stop hook reads the turn the way a PostToolUse hook
    read each call. A call without a result yet has tool_result None.
    """
    results = {m.get("tool_call_id"): m.get("content") for m in messages[start:] if m.get("role") == "tool"}
    calls = []
    for message in messages[start:]:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except (json.JSONDecodeError, TypeError):
                args = {}
            result = results.get(call["id"])
            calls.append({
                "tool_name": call["function"]["name"],
                "tool_input": args if isinstance(args, dict) else {},
                "tool_result": result if not isinstance(result, str) else result[:RESULT_CHARS],
            })
    return calls


def may_stop(messages, start, answer, ended_by="answer"):
    """Run the Stop hooks. Returns None to let the turn end, or the reason to go on.

    ended_by says how the turn is ending: "answer" for a reply without
    tool calls, "finish" for the tool. After MAX_STOP_BLOCKS blocks in one
    turn the hooks are not asked again and the turn ends with a note.
    """
    global BLOCKS
    if BLOCKS >= MAX_STOP_BLOCKS:
        _note(f"the Stop hooks blocked {BLOCKS} times this turn; stopping anyway")
        return None
    outcome = hooks.run_hooks("Stop", {"answer": answer, "calls": turn_calls(messages, start), "blocks": BLOCKS, "ended_by": ended_by})
    if not outcome.blocked:
        return None
    BLOCKS += 1
    return outcome.reason


def send_back(messages, reason):
    """Append the block as a user message, so the agent reads it on the next call."""
    from . import session  # here, not at the top: session imports handoff, which imports the tools

    line = f"Stop blocked: {reason}"
    messages.append({"role": "user", "content": line})
    session.save(messages)
    _note(line)


def reset():
    """Nothing spent, no turn running. Used by the tests."""
    global SPENT, STARTED, SUMMARY, BLOCKS
    SPENT = 0.0
    STARTED = None
    SUMMARY = None
    BLOCKS = 0


def _note(text):
    from .ui import ui  # here, not at the top: ui imports todos, tools imports this module

    ui.note(text)

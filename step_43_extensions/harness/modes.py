"""Step 39 - named permission policies, one layer above the rules.

The rules of step 11 rate a call allow, ask or deny. A mode rewrites that
verdict before anyone is asked. Each mode is a small table: for every
category of call - an edit inside the project, an edit outside it, a bash
command, anything else - which rule verdicts change and into what. A
category the table does not name keeps the verdict the rules gave.

`default` is the rules as they are. `accept-edits` makes an edit inside the
project run without asking, whatever the rules say short of deny.
`read-only` denies every edit and every call the rules would ask about,
so exploration runs and nothing else does. `auto` turns every ask into an
allow: nothing prompts. `plan` is step 28: it sets plan.MODE and the plan
tool set decides; the table for it is empty.

A deny is never rewritten. A rule deny, a session `never` from step 35 and
a hook block all survive every mode, auto included. The OS sandbox of step
12 wraps the command after the verdict and enforces on its own.

CURRENT holds the approval mode. Plan mode is not stored here: it lives in
plan.MODE, so entering plan and approving a plan keep the mode the user had
before, and current() reports "plan" while plan.MODE is "plan".

A change of CURRENT is written to the session log as a {"mode": name}
entry, so --resume comes back in the same mode. Plan mode is not logged:
a plan that was never approved does not survive the session either.
"""

from . import plan, session

MODES = {
    "default": "the rules as they are: read-only commands run, edits inside the project run, the rest asks",
    "accept-edits": "edits inside the project never ask; the bash rules are unchanged",
    "read-only": "edits, memory writes and every call the rules would ask about are denied; exploration runs",
    "auto": "nothing asks; deny rules, session nevers and the sandbox still apply",
    "plan": "read-only tools until a plan is approved (step 28)",
}

NAMES = tuple(MODES)

# mode -> category -> {rule verdict: final verdict}. Only allow and ask appear
# as keys: a deny is final and never reaches the table.
TABLE = {
    "default": {},
    "accept-edits": {
        "edit-inside": {"ask": "allow"},
    },
    "read-only": {
        "edit-inside": {"allow": "deny", "ask": "deny"},
        "edit-outside": {"allow": "deny", "ask": "deny"},
        "bash": {"ask": "deny"},
        "other": {"ask": "deny"},
    },
    "auto": {
        "edit-inside": {"ask": "allow"},
        "edit-outside": {"ask": "allow"},
        "bash": {"ask": "allow"},
        "other": {"ask": "allow"},
    },
    "plan": {},
}

CURRENT = "default"


def current():
    """The mode in force: plan while plan.MODE is plan, otherwise CURRENT."""
    return "plan" if plan.MODE == "plan" else CURRENT


def set_mode(name, log=True):
    """Switch to a mode by name. Returns the name. Raises ValueError for an unknown one.

    `plan` hands over to step 28 and leaves CURRENT alone, so the mode the
    user had comes back when the plan is approved. Any other name leaves
    plan mode, if the harness was in it, and is logged to the session
    unless `log` is False (session.load replaying the log passes that).
    """
    global CURRENT
    if name not in MODES:
        raise ValueError(f"unknown mode {name!r}; one of: {', '.join(NAMES)}")
    if name == "plan":
        plan.set_mode("plan")
        return name
    CURRENT = name
    if plan.MODE == "plan":
        plan.set_mode("act")
    if log:
        session.mode(name)
    return name


def category(name, args, inside_project):
    """Which row of the table a call falls under.

    remember and forget write files too - under the harness home, not the
    project - so they count as an edit inside: read-only denies them.
    """
    if name in ("bash", "bash_background"):
        return "bash"
    if name in ("write_file", "str_replace"):
        return "edit-inside" if inside_project(args.get("path", "")) else "edit-outside"
    if name in ("remember", "forget"):
        return "edit-inside"
    return "other"


def apply(mode, kind, action):
    """The verdict after the mode has its say. A deny stays a deny."""
    if action == "deny":
        return "deny"
    return TABLE[mode].get(kind, {}).get(action, action)


def describe():
    """One line per mode, the current one marked, for /mode."""
    now = current()
    return "\n".join(f"{'*' if name == now else ' '} {name:<13} {text}" for name, text in MODES.items())

"""Step 28 - plan mode: read first, propose a plan, act only after approval.

MODE is "act" or "plan". In plan mode the model is offered read-only tools
plus submit_plan. A submitted plan is validated against PLAN_SCHEMA, drawn
as a panel and put to the user. On yes the steps become todos, MODE flips to
"act" and the plan rides in the late block until every todo is completed.
On no the mode stays "plan" and the user's feedback goes back to the model.
"""

from . import todos

MODE = "act"

READ_ONLY = ("bash", "read_file", "read_skill", "task", "recall")  # offered in plan mode, in this order

PLAN = None     # the approved plan, kept until the todos are all completed
FEEDBACK = []   # what the user said to each rejected plan, newest last

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string", "minLength": 1, "description": "What the work achieves, one sentence"},
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "description": "The step, imperative: 'Add the parser'"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Files this step touches"},
                    "actions": {"type": "array", "items": {"type": "string"}, "description": "What is done to them"},
                },
                "required": ["title", "files", "actions"],
                "additionalProperties": False,
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}, "description": "What could go wrong"},
    },
    "required": ["goal", "steps", "risks"],
    "additionalProperties": False,
}

SUBMIT_PLAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "submit_plan",
        "description": (
            "Propose the plan for the task. The user approves it or sends it back "
            "with feedback. Call it once exploration is done."
        ),
        "parameters": {"type": "object", "properties": {"plan": PLAN_SCHEMA}, "required": ["plan"]},
    },
}


def offered(name):
    """Whether a tool may run in the current mode."""
    return MODE == "act" or name in READ_ONLY or name == "submit_plan"


def toolset():
    """The schemas to offer the model: everything in act mode, read-only plus submit_plan in plan mode."""
    from .tools import TOOL_SCHEMAS  # here, not at the top: tools imports this module

    if MODE == "act":
        return TOOL_SCHEMAS
    by_name = {s["function"]["name"]: s for s in TOOL_SCHEMAS}
    return [by_name[name] for name in READ_ONLY if name in by_name] + [SUBMIT_PLAN_SCHEMA]


def manual_check(plan):
    """The problems with a plan, found by hand. Used when jsonschema is not installed."""
    problems = []

    def string_list(value, where):
        if not isinstance(value, list):
            problems.append(f"{where}: must be a list of strings")
        else:
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    problems.append(f"{where}/{i}: must be a string")

    if not isinstance(plan, dict):
        return ["(root): must be an object"]
    for key in ("goal", "steps", "risks"):
        if key not in plan:
            problems.append(f"(root): '{key}' is a required property")
    for key in plan:
        if key not in PLAN_SCHEMA["properties"]:
            problems.append(f"(root): unexpected property '{key}'")
    if "goal" in plan and (not isinstance(plan["goal"], str) or not plan["goal"]):
        problems.append("goal: must be a non-empty string")
    if "risks" in plan:
        string_list(plan["risks"], "risks")
    if "steps" in plan:
        steps = plan["steps"]
        if not isinstance(steps, list) or not steps:
            problems.append("steps: must be a non-empty list")
        else:
            for i, step in enumerate(steps):
                where = f"steps/{i}"
                if not isinstance(step, dict):
                    problems.append(f"{where}: must be an object")
                    continue
                for key in ("title", "files", "actions"):
                    if key not in step:
                        problems.append(f"{where}: '{key}' is a required property")
                for key in step:
                    if key not in ("title", "files", "actions"):
                        problems.append(f"{where}: unexpected property '{key}'")
                if "title" in step and (not isinstance(step["title"], str) or not step["title"]):
                    problems.append(f"{where}/title: must be a non-empty string")
                for key in ("files", "actions"):
                    if key in step:
                        string_list(step[key], f"{where}/{key}")
    return problems


def validate(plan):
    """The problems with a plan, as strings; an empty list means it is valid."""
    try:
        import jsonschema
    except ImportError:
        return manual_check(plan)
    validator = jsonschema.Draft202012Validator(PLAN_SCHEMA)
    errors = sorted(validator.iter_errors(plan), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in errors]


def render(plan):
    """The plan as text, for the late block."""
    lines = [f"goal: {plan['goal']}"]
    for i, step in enumerate(plan["steps"], 1):
        lines.append(f"{i}. {step['title']}")
        if step["files"]:
            lines.append("   files: " + ", ".join(step["files"]))
        for action in step["actions"]:
            lines.append(f"   - {action}")
    if plan["risks"]:
        lines.append("risks:")
        lines += [f"- {risk}" for risk in plan["risks"]]
    return "\n".join(lines)


def approve(plan):
    """The plan is accepted: its steps become the todos and the mode becomes act."""
    global MODE, PLAN
    PLAN = plan
    FEEDBACK.clear()
    MODE = "act"
    todos.write_todos([{"content": s["title"], "activeForm": s["title"], "status": "pending"} for s in plan["steps"]])


def submit_plan(plan):
    """Validate the plan, show it, and ask the user. Returns the result for the model."""
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if MODE != "plan":
        return "Error: not in plan mode"
    problems = validate(plan)
    if problems:
        return "Error: the plan is invalid:\n" + "\n".join(f"- {p}" for p in problems)
    ui.plan(plan)
    approved, feedback = ui.approve_plan()
    if approved:
        approve(plan)
        return (
            "Plan approved. Mode is now act and every step is a todo. "
            "Work through them in order and mark each one completed."
        )
    FEEDBACK.append(feedback or "(no feedback given)")
    return f"Plan not approved. Still in plan mode. User feedback: {FEEDBACK[-1]}"


def set_mode(mode):
    """Switch modes. Entering plan mode forgets the old plan and its feedback."""
    global MODE, PLAN
    MODE = mode
    if mode == "plan":
        PLAN = None
        FEEDBACK.clear()


def done():
    """True once every todo is completed, or the list is empty."""
    return all(t.get("status") == "completed" for t in todos.TODOS)


def plan_note():
    """The <plan> block for the late injection, or an empty string."""
    global PLAN
    if MODE == "plan":
        text = "You are in plan mode. Read, then call submit_plan. Nothing is written until the user approves."
        if FEEDBACK:
            text += "\nFeedback on rejected plans:\n" + "\n".join(f"- {f}" for f in FEEDBACK)
        return f"\n<plan>\n{text}\n</plan>"
    if PLAN is not None and done():
        PLAN = None  # every step is completed: the plan has served its purpose
    if PLAN is None:
        return ""
    return f"\n<plan>\napproved plan, follow it:\n{render(PLAN)}\n</plan>"

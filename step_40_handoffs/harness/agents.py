"""Step 40 - a definition carries its `name` and its `handoffs` list, the
names it may hand the whole conversation to; None when the front matter
has no list, so the definition takes no part in handoffs (see handoff.py).
The rest is step 36: agent definitions: subagents described in Markdown files.

A file `.agents/agents/<name>.md` has a front matter with `name`,
`description`, an optional `tools` list and an optional `max_turns`, and a
body that is the system prompt. find_agents() reads them the way
skills.find_skills reads SKILL.md files. Each definition becomes one tool,
`agent_<name>`, that runs subagent.loop with that prompt, that tool set and
that turn cap. register() adds the tools to the registry at import, the
way MCP tools join it when their server starts. The main system prompt
lists the definitions, one line each, so the model knows what it can
delegate.

The agent tools are withheld from every subagent, the same as `task`, so
the nesting stays one level deep. A definition may name the edit tools
that the exploration subagent does without; everything else on the
withheld list stays withheld whatever the definition says.
"""

import os
import re
from pathlib import Path

import yaml

from . import subagent
from .skills import front_matter

NAME = re.compile(r"^[A-Za-z0-9_-]{1,50}$")  # a definition name becomes a tool name: letters, digits, _ and -

AGENT_DIRS = [
    Path.home() / ".agents" / "agents",  # your agents
    Path.cwd() / ".agents" / "agents",   # this project's agents
]

PREFIX = subagent.AGENT_PREFIX  # every agent tool is agent_<name>
DEFAULT_MAX_TURNS = 12          # the same cap as the exploration subagent
EDIT_TOOLS = ("write_file", "str_replace")  # withheld from the exploration subagent, but a definition may name them


def parse(text):
    """Split a definition file into its front matter dict and its body."""
    if not text.startswith("---"):
        return None, text
    _, front, body = text.split("---", 2)
    return yaml.safe_load(front) or {}, body.strip()


def as_list(value):
    """A front matter list, or a comma-separated string, as a list of strings; None when absent."""
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",") if part.strip()]
    return [str(item) for item in value] if isinstance(value, list) else None


def find_agents(dirs=None):
    """Read every <name>.md under the agent dirs; name -> definition.

    A later directory wins on a clash, so a project agent replaces a
    personal one of the same name. A file without a name in its front
    matter is skipped.
    """
    agents = {}
    for directory in dirs or AGENT_DIRS:
        for path in sorted(directory.glob("*.md")):
            meta = front_matter(path)  # a broken file is a note, not a crash at import
            if not meta:
                continue
            name = str(meta.get("name") or path.stem)
            if not NAME.match(name):
                print(f"skipped {path}: agent name {name!r} is not letters, digits, _ and - (50 at most)")
                continue
            try:
                max_turns = int(meta.get("max_turns") or DEFAULT_MAX_TURNS)
            except (TypeError, ValueError):
                max_turns = DEFAULT_MAX_TURNS
            _, body = parse(path.read_text(encoding="utf-8-sig", errors="replace"))
            agents[name] = {
                "name": name,
                "description": " ".join(str(meta.get("description", "")).split()),
                "tools": as_list(meta.get("tools")),
                "handoffs": as_list(meta.get("handoffs")),
                "max_turns": max_turns,
                "prompt": body,
                "path": path,
            }
    return agents


AGENTS = find_agents()


def tool_name(name):
    return PREFIX + name


def agents_prompt():
    """One line per definition: the index that goes into the system prompt."""
    return "\n".join(f"- {tool_name(name)}: {a['description']}" for name, a in AGENTS.items())


def toolset(definition):
    """The schemas one definition is offered: its list, or everything, minus the withheld tools."""
    from .tools import TOOL_SCHEMAS, active_schemas

    wanted = definition.get("tools")
    chosen = []
    for schema in TOOL_SCHEMAS:
        name = schema["function"]["name"]
        if subagent.withheld(name, allow=EDIT_TOOLS):
            continue
        if wanted is None or name in wanted:
            chosen.append(schema)
    return active_schemas(chosen)


def system_prompt(definition, cwd=None):
    """The definition's body, then the working directory line every subagent gets."""
    cwd = cwd or os.getcwd()
    return f"{definition['prompt']}\n\nYou are working in {cwd}. Stay inside it. Only your final message is returned to the caller, so it must stand on its own.\n"


def run(name, request, tag=None):
    """Run one named agent on one request and return its final message."""
    definition = AGENTS.get(name)
    if definition is None:
        return f"Error: no agent named '{name}'."
    return subagent.loop(
        system_prompt(definition),
        request,
        toolset(definition),
        definition["max_turns"],
        label=f"{name} working",
        tag=tag,
    )


def make_tool(name):
    """The callable behind agent_<name>: one request in, one report out."""

    def agent_tool(request: str) -> str:
        return run(name, request)

    agent_tool.__name__ = tool_name(name)
    agent_tool.__doc__ = f"Run the {name} agent on one request and return its report."
    return agent_tool


def schema(name):
    """The tool schema for agent_<name>, with the definition's description."""
    definition = AGENTS[name]
    return {
        "type": "function",
        "function": {
            "name": tool_name(name),
            "description": (
                f"{definition['description']} Runs as a subagent with its own context "
                "window; it cannot see this conversation, so the request must stand alone. "
                "Only its final message comes back."
            ),
            "parameters": {
                "type": "object",
                "properties": {"request": {"type": "string", "description": "The task for the agent, written to stand alone"}},
                "required": ["request"],
            },
        },
    }


def register():
    """Add every definition to TOOLS and TOOL_SCHEMAS as agent_<name>. Returns the names."""
    from . import tools as registry  # here, not at the top: tools imports this module

    names = []
    for name in AGENTS:
        full = tool_name(name)
        registry.TOOLS[full] = make_tool(name)
        registry.TOOL_SCHEMAS[:] = [s for s in registry.TOOL_SCHEMAS if s["function"]["name"] != full]
        registry.TOOL_SCHEMAS.append(schema(name))
        names.append(full)
    return names


if __name__ == "__main__":
    print(agents_prompt())

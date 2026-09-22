"""Step 36 - agent definitions: subagents described in Markdown files.

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

AGENT_DIRS = [
    Path.home() / ".agents" / "agents",  # your agents
    Path.cwd() / ".agents" / "agents",   # this project's agents
]

PREFIX = subagent.AGENT_PREFIX  # every agent tool is agent_<name>
DEFAULT_MAX_TURNS = 12          # the same cap as the exploration subagent
EDIT_TOOLS = ("write_file", "str_replace")  # withheld from the exploration subagent, but a definition may name them

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)  # the block between the first two --- lines
NAME = re.compile(r"[A-Za-z0-9_-]{1,50}")  # agent_<name> has to be a tool name the API accepts


def parse(text):
    """Split a definition file into its front matter dict and its body.

    Returns (None, text) when there is no front matter. Raises ValueError
    when the front matter is not a YAML mapping; find_agents turns that
    into a note and skips the file.
    """
    match = FRONT_MATTER.match(text)
    if not match:
        return None, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as broken:
        raise ValueError(f"front matter is not valid YAML: {broken}") from None
    if not isinstance(meta, dict):
        raise ValueError("front matter is not a mapping")
    return meta, text[match.end():].strip()


def tool_list(value):
    """The `tools` field as a list of names: a YAML list, or a comma-separated string. None means every tool."""
    if isinstance(value, str):
        value = [part for part in value.split(",") if part.strip()]
    if not isinstance(value, list):
        return None
    return [str(t).strip() for t in value]


def find_agents(dirs=None):
    """Read every <name>.md under the agent dirs; name -> definition.

    A later directory wins on a clash, so a project agent replaces a
    personal one of the same name. A file without a front matter is
    skipped; a file with a broken one, a bad name or a bad max_turns is
    skipped with a note, so one bad definition never stops the harness
    from starting.
    """
    agents = {}
    for directory in dirs or AGENT_DIRS:
        for path in sorted(directory.glob("*.md")):
            try:
                meta, body = parse(path.read_text(encoding="utf-8-sig"))
                if meta is None:
                    continue
                name = str(meta.get("name") or path.stem)
                if not NAME.fullmatch(name):
                    raise ValueError(f"name {name!r} must match {NAME.pattern}")
                max_turns = int(meta.get("max_turns") or DEFAULT_MAX_TURNS)
            except (OSError, ValueError) as broken:
                _note(f"agent definition {path} skipped: {broken}")
                continue
            agents[name] = {
                "description": " ".join(str(meta.get("description", "")).split()),
                "tools": tool_list(meta.get("tools")),
                "max_turns": max_turns if max_turns > 0 else DEFAULT_MAX_TURNS,
                "prompt": body,
                "path": path,
            }
    return agents


def _note(text):
    from .ui import ui  # here, not at the top: ui imports todos, tools imports this module

    ui.note(text)


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

# Step 40 - Handoffs

**What this step adds:** a handoff moves the whole conversation to
another agent definition. The transcript stays. The system prompt and
the tool set change. The new agent answers the user from then on.
`harness/handoff.py` holds the active agent, the `handoff_to(agent,
reason)` tool, the prompt and tool set of the active agent, and the
switch itself. Three definitions ship for it: `router`, which reads the
request and hands off to a specialist; `coder`, which writes and tests
code; and `reviewer`, which judges a change. Each has a `handoffs:` list
in its front matter that limits who it may hand off to. A handoff to a
name outside the list is an error result the model reads. `/agent`
shows the active agent, `/handoff <name>` forces one, the UI prints a
`handoff -> name` line, and the session log records a `{"handoff":
name}` marker so `--resume` comes back with the right agent.

## Why a handoff and not a subagent

Step 36 gave the harness agent definitions and a way to run one as a
subagent: `agent_planner` gets a request, works in its own context, and
returns one message. That is the right shape when the caller stays in
charge. It is the wrong shape when the caller should step aside.

A router is the clearest case. The user says what they want; the router
reads it, decides who should handle it, and is then done. Running the
specialist as a subagent would put the router between the user and the
specialist for the rest of the session, relaying every message and
paying twice for every turn. The specialist needs the conversation, not
a summary of it, and the user needs to talk to the specialist, not to
the router.

A handoff is the transfer. The messages stay where they are. What
changes is the prefix: the system prompt becomes the new agent's, and
the tools become the new agent's. The next model call is, in every way
that matters, a call to a different agent that happens to know
everything the old one knew.

This is the one place the harness rewrites `messages[0]` on purpose.
Every earlier step kept the prefix stable, because a stable prefix is
what the provider's prompt cache keys on: change one byte at the top and
the whole request is priced as new. The rewrite is still right here. A
handoff is the boundary between two agents, and a new agent with a new
prompt is the point. The cache loss is paid once, at the boundary, and
the transcript after it is cached again from the next call on. A
compaction `<summary>` block in the old prompt is carried over, so the
new agent reads what the old one had condensed.

## The code, piece by piece

### 1. The active agent and its targets

`harness/handoff.py`:

```python
MAIN = "main"     # the name of the default coding agent, which has no definition file
ACTIVE = None     # the active definition, or None for the default agent
PENDING = None    # the name a handoff_to call asked for, until switch() applies it
LAST_REASON = ""  # the reason the model gave for the pending handoff
...
def active_name():
    """The name of the active agent: its definition's name, or `main`."""
    return MAIN if ACTIVE is None else ACTIVE["name"]
...
def targets(active=None):
    """The names the active definition may hand off to, in definition order.

    The default agent may hand off to every definition with a `handoffs`
    list. A definition may hand off to the names on its own list, and only
    to names that exist.
    """
    active = ACTIVE if active is None else active
    if active is None:
        return [name for name, a in agents.AGENTS.items() if a.get("handoffs") is not None]
    return [name for name in active.get("handoffs") or [] if name in agents.AGENTS]
```

`ACTIVE` is one of the definitions `agents.find_agents` read, or `None`
for the default coding agent, which has no file. `targets()` is the
whole policy. A definition takes part in handoffs when its front matter
has a `handoffs` list, and that list is who it may hand off to. The
default agent may hand off to any definition that has a list. A name on
a list that matches no definition is dropped, so a typo in a front
matter cannot become a runtime error.

### 2. The definitions

`.agents/agents/router.md`:

```text
---
name: router
description: Reads the request, decides which specialist should handle it, and hands the conversation off to that specialist.
tools: [bash, read_file, read_skill, task]
handoffs: [coder, reviewer]
max_turns: 6
---
You are the router. You decide who should handle the request, then you hand off.
```

`find_agents` in `harness/agents.py` reads the new key next to `tools`
and stores it as `handoffs`, a list of names, or `None` when the front
matter has no list. It also stores the `name`, so `active_name()` can
read it from the definition.

The router may hand off to `coder` and `reviewer`. The coder may hand
off to `reviewer`, and the reviewer back to `coder`, so a change can go
around the loop: written, judged, fixed, judged again. The `planner` and
`worker` definitions of step 36 have no list, so they take no part: they
stay subagents. A definition with a list is still a subagent tool too;
`agent_coder` exists next to the handoff.

### 3. The tool and the check

`harness/handoff.py`:

```python
def handoff_to(agent: str, reason: str) -> str:
    """Ask for a handoff. The switch happens after this reply's results are in."""
    global PENDING, LAST_REASON
    if agent == active_name():
        return f"Error: {agent} is already the active agent."
    allowed = targets()
    if agent not in allowed:
        if definition(agent) is None and agent != MAIN:
            return f"Error: no agent named '{agent}'. You may hand off to: {', '.join(allowed) or 'nobody'}."
        return f"Error: {active_name()} may not hand off to '{agent}'. You may hand off to: {', '.join(allowed) or 'nobody'}."
    PENDING = agent
    LAST_REASON = reason
    return f"Handing off to {agent}: {reason}. The {agent} agent answers from the next reply on; do not answer the user yourself."
```

The tool does not switch. It checks the name against `targets()`,
records it in `PENDING`, and returns a result. A disallowed name gets an
`Error:` result that names the allowed targets, and nothing else
changes. The switch waits until every tool result of the reply is in,
so the transcript is never cut between a call and its result. The tool
is in `TOOLS` but not in `TOOL_SCHEMAS`: the main loop is offered it
through `toolset()`, and no subagent ever sees it.

### 4. The prompt and the tool set of the active agent

`harness/handoff.py`:

```python
def system_prompt(active, cwd=None):
    """The main system prompt with the definition's body in place of the default role.

    build_system_prompt supplies everything the default agent gets: the
    tool guidance, the agent index, the deferred tools, the instruction
    files and the skills. Only the opening role changes.
    """
    from .llm import build_system_prompt  # here, not at the top: llm imports tools, tools imports this module

    role = None if active is None else active["prompt"]
    return build_system_prompt(cwd, role=role, handoffs=handoff_section(active))


def toolset():
    """The schemas the active agent is offered: the mode's set, cut to the definition's list, plus handoff_to.

    The default agent gets the mode's whole set. A definition with a
    `tools` list gets the mode's set cut to that list; submit_plan stays
    in plan mode whatever the list says. handoff_to is added whenever the
    active agent has a target.
    """
    wanted = None if ACTIVE is None else ACTIVE.get("tools")
    chosen = [s for s in plan.toolset() if wanted is None or s["function"]["name"] in wanted or s["function"]["name"] == "submit_plan"]
    if targets():
        chosen.append(HANDOFF_SCHEMA)
    return chosen
```

`harness/llm.py` takes the opening paragraph as a parameter:

```python
ROLE = """You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Use write_file to create files and str_replace to edit them.
Answer back to the user once exploration is done."""


def build_system_prompt(cwd=None, schemas=None, role=None, handoffs=None):
...
    cwd = cwd or os.getcwd()
    role = ROLE if role is None else role.strip()
    handoffs = handoff_section() if handoffs is None else handoffs
    return f"""
{role}
```

A handed-off prompt is the main prompt with a different first paragraph.
Everything after the role - the todo guidance, the subagent index, the
deferred tools, the instruction files, the skills - is the same for
every agent, so the definition body is what the author wrote and nothing
the harness needs is lost. The `handoffs` section lists the targets of
the active agent with their descriptions, so the model knows who it may
hand off to and why it would.

The tool set composes with the two filters that already exist. `plan.
toolset()` gives the mode's set: everything in act mode, the read-only
tools plus `submit_plan` in plan mode. A definition's `tools` list cuts
that down, and `submit_plan` survives the cut so a handed-off agent can
still plan. `active_schemas()` in `agent.turn` then defers the big
schemas as before.

### 5. The switch and the marker

`harness/handoff.py`:

```python
def apply(name, messages):
...
    global ACTIVE
    from . import compact  # here, not at the top: compact imports llm

    ACTIVE = None if name == MAIN else definition(name)
    if name != MAIN and ACTIVE is None:
        raise KeyError(name)
    if messages and messages[0].get("role") == "system":
        summary = compact.previous_summary(messages[0]["content"])
        prompt = system_prompt(ACTIVE)
        messages[0]["content"] = prompt + ("\n\n" + summary if summary else "")
    return ACTIVE


def switch(messages, name=None, reason=None):
...
    name = PENDING if name is None else name
    reason = LAST_REASON if reason is None else reason
    PENDING = None
    LAST_REASON = ""
    if name is None:
        return None
    if name != MAIN and definition(name) is None:
        ui.note(f"no agent named '{name}'")
        return None
    previous = active_name()
    apply(name, messages)
    session.handoff(name)
    ui.handoff(previous, name, reason)
    return name
```

`apply` is the rewrite: `ACTIVE` changes, and `messages[0]` becomes the
new agent's prompt, with the compaction summary carried over. `switch`
wraps it with the three side effects a live handoff has: the session
marker, the UI line, and the clearing of `PENDING`. `session.load` calls
`apply` alone, because on a resume the marker is being replayed, not
written.

`harness/session.py`:

```python
def handoff(name):
    """Record that `name` answers from here on. The system message on disk stays; load() rewrites it."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"handoff": name}) + NL)
...
        elif "handoff" in entry:
            try:
                handoffs.apply(entry["handoff"], messages)
            except KeyError:
                pass  # the definition file is gone; the transcript loads with the agent it had before
```

The log is append-only, as it has been since step 8, so the system
message on disk keeps the prompt the session started with. The marker
is the record of the change. `load` replays it in place, the way it
replays a `rewind_to` or a `compacted` entry, and the agent that was
answering when the session ended is the one that answers after
`--resume`.

### 6. The loop

`harness/agent.py`:

```python
                message, usage = call_llm(with_mode(messages) + [injection], tools=active_schemas(handoff.toolset()), on_delta=on_delta)
...
        try:
            run_results(messages, message.tool_calls, repeated)
        except KeyboardInterrupt:
            if not steered(messages, "the tool calls"):  # every call has a result by now
                raise
        handoff.switch(messages)  # a handoff_to result in this reply: the next call is the new agent's
```

Two lines. The tool set comes from the active agent instead of from the
mode alone, and after the results of a reply are in, a pending handoff
is applied. The next iteration builds the request from the rewritten
`messages[0]` and the new tool set. `recover()` applies one too: a
crash between a `handoff_to` result and the next call does not lose the
handoff.

### 7. The commands and the env block

`harness/commands.py`:

```python
def agent_info(messages):
    """The active agent, its description and the names it may hand off to."""
    active = handoff.ACTIVE
    what = "the default coding agent" if active is None else active["description"]
    targets = ", ".join(handoff.targets()) or "nobody"
    ui.note(f"active agent: {handoff.active_name()} - {what}; may hand off to: {targets}")
    return messages


def force_handoff(messages, name):
    """Hand the conversation to `name` from the prompt line. The lists do not apply: the user is in charge."""
    if not name:
        ui.note("usage: /handoff <name>; the agents are " + ", ".join(agents_.AGENTS) + ", or main")
        return messages
    handoff.switch(messages, name, "/handoff")
    return messages
```

`/handoff` goes through the same `switch`, so a forced handoff is logged
and drawn like one the model asked for. The lists do not apply to it:
they limit the model, and the user is the one who wrote them. `/handoff
main` returns to the default agent. The `<env>` block of the late
injection carries an `agent:` line next to `mode:`, so the model sees
who it is on every call.

## Run it

```bash
pip install -e .
harness
> /handoff router
> add a --version flag to cli.py
```

The `handoff -> router` line appears at once. The router reads the
request, calls `handoff_to` with `coder`, and the tool panel shows the
result. Then a second line, `handoff -> coder (from router: code is
wanted)`, and the coder's reply follows in the same turn: it reads
`cli.py`, edits it, runs the tests and answers. Type `/agent`:

```text
active agent: coder - Writes, changes and tests code in this project, and hands the conversation to the reviewer when the user wants the work checked.; may hand off to: reviewer
```

Say `check it` and the coder hands off to the reviewer, whose verdict
starts with PASS or FAIL. A FAIL with `fix it` goes back to the coder.
Exit with Ctrl-D, start again with `harness --resume`, and the banner is
followed by the replay and the reviewer is still the active agent: the
marker in the log put it back.

Try a handoff the list forbids. `/handoff coder`, then ask the model to
hand off to the router. The result panel shows `Error: coder may not
hand off to 'router'. You may hand off to: reviewer.` and the coder
answers as itself.

Run the offline tests from the repository root:

```bash
python run_tests.py 40
python check_snippets.py 40
```

## What to notice

- The transcript is the shared state. A handoff copies nothing and
  summarises nothing: the new agent reads the same messages the old one
  did. That is what makes it different from a subagent call.
- The prefix changes once, on purpose. Every earlier step kept
  `messages[0]` stable for the cache. A handoff is the one boundary
  where a new prefix is the feature, and the loss is paid once.
- The switch is deferred. `handoff_to` returns a result like any tool;
  the loop applies the handoff after every result of the reply is in.
  The transcript is never cut between a call and its result, and a
  reply with a handoff and other calls keeps all of them.
- The lists are the policy, and they are in the files. Who may hand off
  to whom is front matter, next to which tools each agent has. The
  harness enforces it with one function, `targets()`.
- The default agent is a name, not a file. `main` has no definition;
  `ACTIVE = None` stands for it, and `/handoff main` is the way back.
- The marker is small. The log gains one line per handoff, and the
  prompt is rebuilt on load from the definition, so a changed
  definition file is picked up by the next resume.
- Compaction still works. The summary block rides through the rewrite,
  and the next compaction starts from the new agent's prompt.
- A handed-off agent is a main agent. It gets the todo list, the memory,
  the jobs, the subagents and the hooks, because its prompt is built by
  `build_system_prompt` and its tools come from the same registry.

## Diff from step 39

```bash
diff -r ../step_39_approval_modes/harness harness
```

Added: `handoff.py` (`MAIN`, `ACTIVE`, `PENDING`, `LAST_REASON`,
`HANDOFF_SCHEMA`, `HANDOFF_INTRO`, `active_name`, `definition`,
`targets`, `handoff_section`, `system_prompt`, `toolset`, `handoff_to`,
`apply`, `switch`, `reset`), `.agents/agents/router.md`,
`.agents/agents/coder.md`. Changed: `.agents/agents/reviewer.md`
(`handoffs: [coder]` and a paragraph for the handed-off case),
`agents.py` (`name` and `handoffs` in a definition), `llm.py` (`ROLE`,
`build_system_prompt(role, handoffs)`, the handoff section in the
prompt), `tools.py` (`handoff_to` in `TOOLS`), `agent.py`
(`handoff.toolset()`, `handoff.switch` after the results and in
`recover`), `session.py` (`handoff` marker, `load` applies it),
`commands.py` (`/agent`, `/handoff`), `context.py` (`agent:` in
`<env>`), `ui.py` (`handoff` line, the banner). Everything else,
`capstone/` included, is unchanged from step 39.

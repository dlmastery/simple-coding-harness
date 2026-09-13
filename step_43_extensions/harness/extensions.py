"""Step 43 - extensions: one registry that every add-on registers through.

An extension is a Python module with one function, `apply(ctx)`. The
harness imports the module, builds a Context for it and calls `apply`.
The context offers five registrations:

    ctx.tool(fn, schema=None)          a tool the model may call
    ctx.command(name, help, fn)        a slash command for the prompt line
    ctx.hook(event, fn, matcher="*")   a hook, called with the event dict
    ctx.prompt_section(text)           a paragraph of the system prompt
    ctx.agent(definition)              an agent definition, with its agent_<name> tool

Every registration is recorded on the extension, so `/extensions` can
list what each one added and `unload` can take it back. A module that
fails to import, has no `apply`, or raises inside it is skipped with a
note; the registrations it made before the failure are removed.

Two kinds of extension exist. The built-in ones are the harness's own
loaders - skills, hooks, agents and MCP - which used to write into the
tool registry and the hook list by hand and now go through the same
five calls as everything else. They are applied when the tool registry
is built. The project's extensions are `.agents/extensions/*.py`, and
the user's are `~/.simple-harness/extensions/*.py`; they are loaded
after the built-in ones, so they may replace what a built-in registered.

A tool registration under a name that exists replaces it in place, so
the tool keeps its position in the list the model sees; a command or an
agent under a name that exists is replaced the same way, and unload puts
the old one back. Hooks and prompt sections are appended. The registry
holds the commands, the hooks and the prompt sections itself; the tools
live in tools.TOOLS and tools.TOOL_SCHEMAS, and the agents in
agents.AGENTS, where the rest of the harness already reads them.
"""

import importlib
import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path

EXTENSION_DIRS = [
    Path.home() / ".simple-harness" / "extensions",  # your extensions, every project
    Path.cwd() / ".agents" / "extensions",           # this project's extensions
]

BUILTIN = (  # (extension name, module) - the harness's own loaders, applied in this order
    ("skills", "harness.skills"),
    ("hooks", "harness.hooks"),
    ("agents", "harness.agents"),
    ("mcp", "harness.mcp_client"),
)

KINDS = ("tool", "command", "hook", "section", "agent")

TYPES = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}

EXTENSIONS = {}      # name -> Extension, in load order
COMMANDS = {}        # "/name" -> (help, fn); fn(messages, arg) returns the messages
HOOKS = {}           # event -> [{"matcher": ..., "function": fn, "source": extension name}]
PROMPT_SECTIONS = []  # (extension name, text or callable) in registration order


@dataclass
class Registration:
    """One thing an extension added: its kind, its name, and the entry to remove."""

    kind: str
    name: str
    entry: object = None  # what unload needs: the hook dict or section tuple to drop, or the tool or command to put back


@dataclass
class Extension:
    """One loaded module: where it came from, whether it applied, and what it registered."""

    name: str
    path: Path | None = None  # None for a built-in
    status: str = "loaded"    # "loaded", or "failed: <why>"
    registrations: list = field(default_factory=list)

    @property
    def source(self):
        """Where the extension came from: built-in, or its file relative to the project."""
        if self.path is None:
            return "built-in"
        try:
            return self.path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return str(self.path)

    def record(self, kind, name, entry=None):
        """Remember a registration. A repeat of a tool, command or agent name replaces the old record."""
        if kind in ("tool", "command", "agent"):
            self.registrations = [r for r in self.registrations if (r.kind, r.name) != (kind, name)]
        self.registrations.append(Registration(kind, name, entry))

    def summary(self):
        """`tool a, b; command /x` - what the extension added, grouped by kind."""
        parts = []
        for kind in KINDS:
            names = [r.name for r in self.registrations if r.kind == kind]
            if names:
                parts.append(f"{kind} {', '.join(names)}")
        return "; ".join(parts) or "-"


class Context:
    """What `apply(ctx)` receives: the five registrations, bound to one extension."""

    def __init__(self, extension):
        self.extension = extension

    def tool(self, fn, schema=None):
        """Register a tool. Without a schema, one is built from the signature and the docstring."""
        from . import tools as registry  # here, not at the top: tools imports this module

        schema = schema or schema_from(fn)
        name = schema["function"]["name"]
        previous = (registry.TOOLS.get(name), find_schema(name))  # what unload puts back
        registry.TOOLS[name] = fn
        for i, existing in enumerate(registry.TOOL_SCHEMAS):
            if existing["function"]["name"] == name:
                registry.TOOL_SCHEMAS[i] = schema  # in place: the tool keeps its position
                break
        else:
            registry.TOOL_SCHEMAS.append(schema)
        self.extension.record("tool", name, previous)
        return name

    def command(self, name, help, fn):
        """Register a slash command. fn(messages, arg) returns the messages; arg is the text after the name."""
        name = name if name.startswith("/") else "/" + name
        previous = COMMANDS.get(name)
        COMMANDS[name] = (help, fn)
        self.extension.record("command", name, previous)
        return name

    def hook(self, event, fn, matcher="*"):
        """Register a hook for one event. fn(event) answers like a python hook: a dict or None."""
        entry = {"matcher": matcher, "function": fn, "source": self.extension.name}
        HOOKS.setdefault(event, []).append(entry)
        self.extension.record("hook", f"{event}:{matcher}", entry)
        return entry

    def prompt_section(self, text):
        """Register a paragraph of the system prompt: a string, or a function that returns one."""
        entry = (self.extension.name, text)
        PROMPT_SECTIONS.append(entry)
        label = text.__name__ if callable(text) else " ".join(str(text).split()[:3]) + "..."
        self.extension.record("section", label, entry)
        return entry

    def agent(self, definition):
        """Register an agent definition and its agent_<name> tool. Returns the tool name."""
        from . import agents  # here, not at the top: agents is itself a built-in extension

        definition = agents.normalise(definition)
        name = definition["name"]
        previous = agents.AGENTS.get(name)  # what unload puts back
        agents.AGENTS[name] = definition
        self.extension.record("agent", name, previous)
        return self.tool(agents.make_tool(name), agents.schema(name))


def find_schema(name):
    """The registered schema of a tool, or None."""
    from . import tools as registry  # here, not at the top: tools imports this module

    return next((s for s in registry.TOOL_SCHEMAS if s["function"]["name"] == name), None)


def schema_from(fn):
    """A tool schema from a function: the name, the first docstring line, and the typed parameters."""
    properties = {}
    required = []
    for parameter in inspect.signature(fn).parameters.values():
        kind = TYPES.get(parameter.annotation, "string")
        properties[parameter.name] = {"type": kind}
        if parameter.default is inspect.Parameter.empty:
            required.append(parameter.name)
    description = (inspect.getdoc(fn) or fn.__name__).strip().splitlines()[0]
    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


# --- loading -------------------------------------------------------------------


def context(name):
    """The context of a named extension, created on first use. A built-in that registers late uses this."""
    extension = EXTENSIONS.get(name)
    if extension is None:
        extension = EXTENSIONS[name] = Extension(name)
    return Context(extension)


def apply_module(name, module, path=None):
    """Run one module's apply(ctx) as the extension `name`. Returns the Extension, loaded or failed."""
    if name in EXTENSIONS:
        unload(name)  # a reload replaces what the old copy registered
    extension = EXTENSIONS[name] = Extension(name, path)
    apply = getattr(module, "apply", None)
    if not callable(apply):
        return _failed(extension, "no apply(ctx) function")
    try:
        apply(Context(extension))
    except Exception as failed:  # noqa: BLE001 - one broken extension must not stop the harness
        return _failed(extension, f"{type(failed).__name__}: {failed}")
    return extension


def load_file(path):
    """Import one extension file and apply it. Its name is the file's stem."""
    name = path.stem
    try:
        spec = importlib.util.spec_from_file_location(f"harness_extension_{name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as failed:  # noqa: BLE001 - a file that does not import is a failed extension
        return _failed(Extension(name, path), f"{type(failed).__name__}: {failed}")
    return apply_module(name, module, path)


def load(dirs=None):
    """Load every *.py under the extension dirs, user first, then project. Returns the extensions loaded."""
    loaded = []
    for directory in EXTENSION_DIRS if dirs is None else dirs:
        for path in sorted(Path(directory).glob("*.py")):
            if path.name.startswith("_"):
                continue  # _helpers.py and the like: imported by extensions, not one itself
            loaded.append(load_file(path))
    return loaded


def load_builtin():
    """Apply the harness's own loaders, in BUILTIN order. Returns the extensions."""
    return [apply_module(name, importlib.import_module(module)) for name, module in BUILTIN]


def unload(name):
    """Remove every registration of one extension and forget it."""
    from . import agents  # here, not at the top: agents is itself a built-in extension
    from . import tools as registry

    extension = EXTENSIONS.pop(name, None)
    if extension is None:
        return
    for registration in reversed(extension.registrations):
        if registration.kind == "tool":
            fn, schema = registration.entry  # the tool the name had before, or (None, None)
            registry.TOOLS.pop(registration.name, None)
            if fn is not None:
                registry.TOOLS[registration.name] = fn
            for i, existing in enumerate(registry.TOOL_SCHEMAS):
                if existing["function"]["name"] == registration.name:
                    if schema is None:
                        del registry.TOOL_SCHEMAS[i]
                    else:
                        registry.TOOL_SCHEMAS[i] = schema  # the old schema, back in the same place
                    break
        elif registration.kind == "command":
            COMMANDS.pop(registration.name, None)
            if registration.entry is not None:
                COMMANDS[registration.name] = registration.entry
        elif registration.kind == "hook":
            for hooks in HOOKS.values():
                hooks[:] = [h for h in hooks if h is not registration.entry]
        elif registration.kind == "section":
            PROMPT_SECTIONS[:] = [s for s in PROMPT_SECTIONS if s is not registration.entry]
        elif registration.kind == "agent":
            agents.AGENTS.pop(registration.name, None)
            if registration.entry is not None:
                agents.AGENTS[registration.name] = registration.entry


def _failed(extension, why):
    """Mark an extension failed, drop what it registered so far, and say so."""
    unload(extension.name)
    extension.status = f"failed: {why}"
    extension.registrations = []
    EXTENSIONS[extension.name] = extension
    _note(f"extension {extension.name!r} skipped: {why}")
    return extension


# --- what the rest of the harness reads ------------------------------------------


def hooks_for(event):
    """The registered hooks of one event, in registration order."""
    return list(HOOKS.get(event, []))


def prompt_sections():
    """Every registered section, rendered, in order, separated by a blank line."""
    rendered = []
    for _, text in PROMPT_SECTIONS:
        value = text() if callable(text) else text
        if value and str(value).strip():
            rendered.append(str(value).strip())
    return "\n\n".join(rendered)


def label(name):
    """How a registration's source reads in a listing: built-in, or the extension's name."""
    extension = EXTENSIONS.get(name)
    return "built-in" if extension is not None and extension.path is None else name


def summary():
    """One row per extension for /extensions: name, status, source and what it registered."""
    return [f"{e.name:<12} {e.status:<8} {e.source:<36} {e.summary()}" for e in EXTENSIONS.values()]


def _note(text):
    from .ui import ui  # here, not at the top: ui imports todos, tools imports this module

    ui.note(text)

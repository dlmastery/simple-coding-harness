"""The one skills harness: boot a pack, run the model loop, route every tool
call through `execute()`.

`boot` reads `SKILL.md` (the body becomes the system prompt), `tools.md`
(the allowed set) and appends the pack's sibling files - schema, loop, graph,
paths, memory (unless MEMORY_OFF), eval, policies, templates - to the prompt
verbatim. `run` is the stage-15 loop: call the model, run each tool call
through `execute`, append the result, repeat; stop when the model answers in
text or the call cap is hit. The budget stops the fits, not the loop: a
25th `fit_recipe` is an `Error:` result the model reads.

Python here never decides what to fit. It supplies tools and a transcript.
"""

import json
import os
from pathlib import Path

from common import packs, tasks
from common.approve import Human, Proposals
from common.budget import Budget
from common.gate import LockedTest
from common.trace import TraceLog

MAX_CALLS = 400   # model calls per boot; a pack that never answers in text stops here


def memory_off_env():
    return os.environ.get("MEMORY_OFF", "").lower() in ("1", "true", "yes")


class Run:
    """Everything one boot of one pack owns: the prompt, the allowed tools, the task, the budget, the log."""

    def __init__(self, pack_dir, task, *, seed=0, arm="memory", run_dir=None, human=None, target=None, quiet=False, memory_off=None):
        self.pack_dir = Path(pack_dir)
        self.task = task
        self.seed = seed
        self.arm = arm
        self.problem = task["name"]
        self.files = packs.read_pack(self.pack_dir)
        self.meta, self.body = packs.parse_front_matter(self.files["SKILL.md"])
        self.allowed = packs.allowed_tools(self.files.get("tools.md", ""))
        self.run_dir = Path(run_dir) if run_dir else self.pack_dir.parent.parent / "runs" / self.meta["name"]
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.target = Path(target) if target else self.pack_dir   # the pack a verifier / meta pack writes to
        self.memory_path = self.target / "memory.json"
        self.memory_off = memory_off_env() if memory_off is None else bool(memory_off)
        self.memory_frozen = False
        self.budget = Budget(json.loads(self.files["schema.json"])["n_fits"] if "schema.json" in self.files else 0)
        self.trace = TraceLog(self.run_dir / "traces.jsonl")
        self.gate = LockedTest(lambda rec: tasks.score_on(task, seed, rec, "test"), self.budget)
        self.human = human or Human.from_env()
        self.proposals = Proposals(self.human, quiet=quiet)
        self.versions_dir = self.run_dir / "versions"
        self.fits = []            # this boot's fit rows, in order
        self.messages = []
        self.calls = 0
        self.visits = {}          # per-visit counters the gated tools keep (patch_pack, private_score)
        self.loaded = False
        self.system = self.build_prompt()
        self.trace.append(event="boot", problem=self.problem, arm=arm, seed=seed,
                          info={"pack": self.meta["name"], "checksums": packs.checksums(self.pack_dir), "memory_off": self.memory_off})

    def build_prompt(self):
        """SKILL.md body, then every sibling file the pack ships, each under a `### FILE:` header."""
        parts = [self.body.strip()]
        for name in sorted(self.files):
            if name == "SKILL.md" or not name.startswith(packs.PROMPT_FILES):
                continue
            if name == "memory.json" and self.memory_off:
                parts.append("### FILE: memory.json\n(MEMORY_OFF: the cards are not loaded this run)")
                continue
            parts.append(f"### FILE: {name}\n{self.files[name].strip()}")
        if self.target != self.pack_dir and self.memory_path.exists() and not self.memory_off:
            # a verifier or meta pack reads the pack it writes to: its cards are in the prompt, its transcript is not
            parts.append(f"### FILE: memory.json\n{self.memory_path.read_text(encoding='utf-8').strip()}")
        parts.append(f"### PROBLEM\n{json.dumps({k: self.task[k] for k in ('name', 'title', 'metric', 'budget')})}")
        return "\n\n".join(parts)

    @property
    def splits(self):
        return tasks.splits(self.task, self.seed)

    @property
    def profile(self):
        return tasks.profile(self.task)

    def transcript_text(self):
        return "\n".join(str(m.get("content") or "") for m in self.messages)


def boot(pack_dir, task, **kw):
    return Run(pack_dir, task, **kw)


def entry(reply):
    """A model reply as a transcript entry: role, content and tool calls, nothing else."""
    e = {"role": "assistant", "content": reply.get("content")}
    if reply.get("tool_calls"):
        e["tool_calls"] = [{"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}}
                           for c in reply["tool_calls"]]
    return e


def run(session, model, max_calls=MAX_CALLS, user="Begin. Follow the procedure in your instructions."):
    """The loop. `model(messages, tool_schemas) -> {content, tool_calls}`; every call goes through execute()."""
    from common.tools import execute, schemas_for

    session.messages = [{"role": "system", "content": session.system}, {"role": "user", "content": user}]
    schemas = schemas_for(session.allowed)
    for _ in range(max_calls):
        reply = model(session.messages, schemas)
        session.calls += 1
        session.messages.append(entry(reply))
        if not reply.get("tool_calls"):
            break
        for call in reply["tool_calls"]:
            result = execute(session, call)
            session.messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    session.trace.append(event="stop", problem=session.problem, arm=session.arm, seed=session.seed,
                         info={"calls": session.calls, "fits": session.budget.used})
    return session


def openai_model():
    """The real model, from BASE_URL / API_KEY / MODEL like the rest of the repo. Same reply shape as the fake."""
    from openai import OpenAI

    client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])
    name = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

    def call(messages, tool_schemas):
        response = client.chat.completions.create(model=name, messages=messages, tools=tool_schemas or None)
        if not response.choices:
            raise RuntimeError(getattr(response, "error", None) or "empty reply")
        m = response.choices[0].message
        return {"content": m.content,
                "tool_calls": [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments} for c in (m.tool_calls or [])]}
    return call


def choose_model():
    """FAKE_MODEL=1 -> the scripted fake; otherwise the real model, which needs a key like the rest of the repo."""
    if os.environ.get("FAKE_MODEL") == "1":
        from common.fake import FakeModel
        return FakeModel()
    if not os.environ.get("API_KEY"):
        raise SystemExit("set BASE_URL / API_KEY / MODEL for a live run, or FAKE_MODEL=1 for the scripted fake")
    return openai_model()

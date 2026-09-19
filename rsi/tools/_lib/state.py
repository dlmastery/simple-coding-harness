"""The run state on disk: what one arm of one pack on one task has spent.

`runs/<pack>/<task>/state.json` under the lesson directory holds one entry per
arm and seed - fits used, frozen, test scored, the fit rows - and
`traces.jsonl` next to it is the append-only log every arm writes to. The
budget, the FREEZE gate and the locked test are these numbers: `fit_recipe`
refuses the 25th fit because `used` says 24, `score_test` refuses before
FREEZE because `frozen` says false and refuses a second time because
`test_scored` says true. There is no object in memory that could forget;
every script starts from the file.

The pack itself is the other half of the state (`memory.json`, `versions/`,
`config.json` with the off switches). Where the runs directory is:
`--run <dir>` if given, else `RSI_RUNS` if set, else `<lesson>/runs/`, where
the lesson directory is the one holding `.claude/` or `.agents/`
(`<pack>/../../..`, i.e. the lesson), or the pack's parent when the pack sits on its own.
"""

import json
import os
from pathlib import Path

from _lib import packs, tasks
from _lib.trace import TraceLog


def fix_path(p):
    """A Git Bash path (/c/Users/...) as Windows Python reads it (C:/Users/...); anything else unchanged."""
    p = str(p)
    if len(p) > 2 and p[0] == "/" and p[1].isalpha() and (len(p) == 2 or p[2] == "/") and not Path(p).exists():
        return f"{p[1].upper()}:{p[2:] or '/'}"
    return p


def pack_name(pack_dir):
    """The pack's name: SKILL.md's front matter, else the directory's name."""
    skill = Path(pack_dir) / "SKILL.md"
    if skill.exists():
        try:
            meta, _ = packs.parse_front_matter(skill.read_text(encoding="utf-8"))
            return str(meta["name"])
        except ValueError:
            pass
    return Path(pack_dir).name


def lesson_dir(pack_dir):
    """The directory the agent was opened in: the one holding .claude/ or .agents/ above the pack."""
    pack_dir = Path(pack_dir).resolve()
    for parent in pack_dir.parents:
        if parent.name in (".claude", ".agents"):
            return parent.parent
    return pack_dir.parent


def runs_root(pack_dir, run=None):
    if run:
        return Path(run)
    if os.environ.get("RSI_RUNS"):
        return Path(os.environ["RSI_RUNS"])
    return lesson_dir(pack_dir) / "runs"


def config(pack_dir):
    """The pack's config.json: the off switches (`memory: off`, `meta: off`) and the clock (`k`). Missing = {}."""
    path = Path(pack_dir) / "config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def memory_off(pack_dir, arm_state=None):
    """MEMORY_OFF: the pack says so in config.json, or this arm was opened with --memory off."""
    return config(pack_dir).get("memory") == "off" or bool(arm_state and arm_state.get("memory_off"))


class Run:
    """One (pack, task, arm, seed): its state entry, its trace log, its task and profile."""

    def __init__(self, pack_dir, task_path, arm="memory", seed=0, run=None):
        self.pack_dir = Path(fix_path(pack_dir)).resolve()
        if not (self.pack_dir / "SKILL.md").exists():
            raise ValueError(f"no SKILL.md under {self.pack_dir}: --pack names a skill pack directory")
        self.task_path = Path(fix_path(task_path))
        self.task = tasks.load_task(self.task_path)
        self.arm = arm
        self.seed = int(seed)
        self.pack = pack_name(self.pack_dir)
        self.problem = self.task["name"]
        self.root = runs_root(self.pack_dir, run) / self.pack / self.problem
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self.trace = TraceLog(self.root / "traces.jsonl")
        self.files = packs.read_pack(self.pack_dir)
        self.meta, self.body = packs.parse_front_matter(self.files["SKILL.md"])
        self.all_state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {"arms": {}}

    # ---------------------------------------------------------------- the arm's entry

    @property
    def key(self):
        return f"{self.arm}/{self.seed}"

    @property
    def opened(self):
        return self.key in self.all_state["arms"]

    @property
    def arm_state(self):
        if not self.opened:
            raise ValueError(f"arm {self.arm!r} seed {self.seed} of {self.pack} on {self.problem} is not open: run load_splits.py first")
        return self.all_state["arms"][self.key]

    def open(self, memory_off_flag=False, memory_frozen=False):
        """load_splits: create the arm's entry with the budget from schema.json / loop.json; a second open is a no-op."""
        if self.opened:
            return self.arm_state
        n = self.n_fits()
        self.all_state["arms"][self.key] = {
            "pack": self.pack, "task": self.problem, "arm": self.arm, "seed": self.seed, "n_fits": n,
            "fits_used": 0, "frozen": n == 0, "test_scored": False, "test_score": None, "test_recipe": None,
            "memory_off": bool(memory_off_flag), "memory_frozen": bool(memory_frozen),
            "checksums": packs.checksums(self.pack_dir), "fits": [],
        }
        self.save()
        return self.arm_state

    def n_fits(self):
        """The budget the pack declares: schema.json n_fits, else loop.json N, else 0 (a pack that never fits)."""
        if "schema.json" in self.files:
            return int(json.loads(self.files["schema.json"]).get("n_fits", 0))
        if "loop.json" in self.files:
            return int(json.loads(self.files["loop.json"]).get("N", 0))
        return 0

    def save(self):
        with open(self.state_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self.all_state, f, indent=1)
            f.write("\n")

    # ---------------------------------------------------------------- the gates as numbers

    @property
    def left(self):
        s = self.arm_state
        return 0 if s["frozen"] else s["n_fits"] - s["fits_used"]

    def spend(self):
        """Count one fit before it happens; the 25th raises. An error still counts: a wasted fit is a fit."""
        s = self.arm_state
        if s["frozen"] or s["fits_used"] >= s["n_fits"]:
            raise ValueError(f"budget of {s['n_fits']} fits used; fit {s['fits_used'] + 1} refused (FREEZE)")
        s["fits_used"] += 1
        if s["fits_used"] >= s["n_fits"]:
            s["frozen"] = True
        return s["fits_used"]

    def freeze(self):
        """FREEZE: no more fits for this arm, whatever is left of the budget. Opens the locked test."""
        s = self.arm_state
        s["frozen"] = True
        self.save()
        return s

    def score_test_once(self, rec):
        s = self.arm_state
        if not s["frozen"]:
            raise ValueError(f"the test split is locked until FREEZE: {self.left} fits remain (or run freeze.py to forfeit them)")
        if s["test_scored"]:
            raise ValueError("the test split was scored once already; there is no second look")
        score = tasks.score_on(self.task, self.seed, rec, "test")
        s["test_scored"], s["test_score"], s["test_recipe"] = True, score, rec
        self.save()
        return score

    # ---------------------------------------------------------------- convenience

    @property
    def profile(self):
        return tasks.profile(self.task)

    @property
    def memory_path(self):
        return self.pack_dir / "memory.json"

    @property
    def memory_off(self):
        return memory_off(self.pack_dir, self.all_state["arms"].get(self.key))

    @property
    def versions_dir(self):
        return self.root.parent / "versions"      # per pack, across problems: generation n+1 boots what n wrote

    def log(self, event, **info):
        """One trace row for this arm: recipe / val_score / error are fields, everything else goes under info."""
        row = {k: info.pop(k) for k in ("recipe", "val_score", "error", "seconds") if k in info}
        self.trace.append(event=event, problem=self.problem, arm=self.arm, seed=self.seed, info=info or None, **row)

    def fit_rows(self, arm=None, seed=None, problem=None):
        """The fit rows of one arm (default this one) from the trace, in order."""
        match = {"problem": self.problem if problem is None else problem}
        if arm != "*":
            match["arm"] = self.arm if arm is None else arm
        if seed != "*":
            match["seed"] = self.seed if seed is None else seed
        return self.trace.rows("fit", **match)

    def all_traces(self):
        """Every fit row of this pack on every problem (the `all` scope): the sibling runs/<pack>/*/traces.jsonl."""
        rows = []
        for path in sorted(self.root.parent.glob("*/traces.jsonl")):
            rows += TraceLog(path).rows("fit")
        return rows


def require_tool(pack_dir, name):
    """The pack's tools.md -> Allowed must name this tool, or the script refuses: the file declares, the script enforces.
    A pack without tools.md allows everything (a bare directory is not a pack contract)."""
    tools_md = Path(pack_dir) / "tools.md"
    if not tools_md.exists():
        return
    allowed = packs.allowed_tools(tools_md.read_text(encoding="utf-8"))
    if name not in allowed:
        raise ValueError(f"{name} is not in {pack_name(pack_dir)}'s tools.md -> Allowed; it is not available to this pack")

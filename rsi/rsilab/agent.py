"""The research agent: an AIDE-style draft / debug / improve loop driven by harness files.

The model is frozen. Everything else is read from a harness directory, so an
improver can change the agent by editing files, exactly as in Meta-Harness and
Harness^2:

    system.md     system prompt
    draft.md      prompt for a first solution        ({description} {data_preview} {timeout})
    improve.md    prompt to improve the best node    (+ {code} {output} {score} {direction})
    debug.md      prompt to repair a failed node     (+ {code} {output})
    skills/*.md   playbooks appended to the system prompt
    memory.md     lessons carried between competitions (when config.memory is true)
    config.json   model, steps, drafts, debug depth, timeouts, preview size

One attempt = `config.steps` generated scripts. Each script runs in its own
directory with the competition's public data at ./input. The agent picks the
node with the best self-reported VALIDATION_SCORE; the grader later scores that
node's submission on hidden answers the agent never sees.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import llm, mle

EXEC_CACHE = llm.CACHE_DIR / "exec.jsonl"
_exec_lock = threading.Lock()
_exec_cache = None


@dataclass
class Node:
    step: int
    stage: str                 # draft | improve | debug
    parent: int = None
    plan: str = ""
    code: str = ""
    output: str = ""
    ok: bool = False           # ran, printed a score, wrote a well-formed submission
    val: float = None          # self-reported VALIDATION_SCORE
    seconds: float = 0.0
    grade: dict = None         # hidden grade of this node's submission (never shown to the agent)


@dataclass
class Attempt:
    competition: str
    replica: int
    nodes: list = field(default_factory=list)
    best: int = None
    tokens: int = 0
    calls: int = 0

    @property
    def final(self):
        return self.nodes[self.best].grade if self.best is not None else {"beats": 0.0, "above_median": False,
                                                                          "any_medal": False, "score": None, "valid": False}

    @property
    def exec_seconds(self):
        return sum(n.seconds for n in self.nodes)

    def to_json(self):
        return {**asdict(self), "final": self.final, "exec_seconds": self.exec_seconds}


def load_harness(path):
    path = Path(path)
    h = {"config": json.loads((path / "config.json").read_text(encoding="utf-8"))}
    for name in ("system", "draft", "improve", "debug"):
        h[name] = (path / f"{name}.md").read_text(encoding="utf-8")
    skills = sorted((path / "skills").glob("*.md")) if (path / "skills").exists() else []
    h["skills"] = {p.name: p.read_text(encoding="utf-8") for p in skills}
    mem = path / "memory.md"
    h["memory"] = mem.read_text(encoding="utf-8") if mem.exists() else ""
    return h


def system_prompt(h):
    parts = [h["system"].strip()]
    for name, text in h["skills"].items():
        parts.append(f"## Skill: {name[:-3]}\n\n{text.strip()}")
    if h["config"].get("memory") and h["memory"].strip():
        parts.append(f"## Lessons from earlier competitions\n\n{h['memory'].strip()}")
    return "\n\n".join(parts)


def data_preview(public, rows):
    """List the public files; show the first rows of each CSV (truncated: some rows are long)."""
    lines = []
    for p in sorted(public.rglob("*")):
        if p.is_dir() or p.name == "description.md":
            continue
        rel = p.relative_to(public).as_posix()
        lines.append(f"- {rel} ({p.stat().st_size / 1e6:.1f} MB)")
        if p.suffix == ".csv" and rows:
            with open(p, encoding="utf-8", errors="replace") as f:
                head = [next(f, "").rstrip("\n")[:300] for _ in range(rows + 1)]
            lines += ["    " + l for l in head if l]
        if p.suffix == ".json" and rows:
            with open(p, encoding="utf-8", errors="replace") as f:
                lines.append("    " + f.read(600).replace("\n", " ") + " ...")
        if len(lines) > 60:
            lines.append("- ...")
            break
    return "\n".join(lines)


def render(template, values):
    """Fill {name} placeholders. Plain replace, so braces elsewhere in an edited prompt are safe."""
    for k, v in values.items():
        template = template.replace("{" + k + "}", str(v))
    return template


def extract_code(text):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    return max(blocks, key=len) if blocks else ""


def _link_input(run_dir, public):
    target = run_dir / "input"
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(public), str(target))
    else:
        target.symlink_to(public, target_is_directory=True)


def _submission_ok(path, sample):
    try:
        import pandas as pd
        sub, ref = pd.read_csv(path), pd.read_csv(sample)
        return list(sub.columns) == list(ref.columns) and len(sub) == len(ref)
    except Exception:
        return False


def _exec_load():
    global _exec_cache
    if _exec_cache is None:
        _exec_cache = {}
        if EXEC_CACHE.exists():
            for line in EXEC_CACHE.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    _exec_cache[row["key"]] = row
    return _exec_cache


def execute(cid, code, run_dir, timeout):
    """Run one script; grade its submission. Cached by (competition, code) for replay."""
    key = hashlib.sha256(f"{cid}\n{timeout}\n{code}".encode("utf-8")).hexdigest()
    with _exec_lock:
        hit = _exec_load().get(key)
    if hit:
        return hit
    if os.environ.get("RSI_LLM") == "replay":
        raise llm.ReplayMiss(f"no cached execution for this script on {cid}")
    comp = mle.get(cid)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "submission").mkdir(exist_ok=True)
    (run_dir / "solution.py").write_text(code, encoding="utf-8")
    if not (run_dir / "input").exists():
        _link_input(run_dir, comp.public)
    start = time.time()
    try:
        proc = subprocess.run([sys.executable, "solution.py"], cwd=run_dir, capture_output=True, text=True,
                              timeout=timeout, env={**os.environ, "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "4"})
        output = (proc.stdout + proc.stderr)[-3000:]
        code_ok = proc.returncode == 0
    except subprocess.TimeoutExpired as e:
        output = ((e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""))[-2000:]
        output += f"\nTimeoutError: the script exceeded {timeout} seconds"
        code_ok = False
    seconds = time.time() - start
    found = re.findall(r"VALIDATION_SCORE:\s*([-+0-9.eE]+|nan|inf)", output)
    val = None
    try:
        val = float(found[-1]) if found else None
    except ValueError:
        pass
    sub = run_dir / "submission" / "submission.csv"
    sample = next(comp.public.glob("sample*ubmission*.csv"), None)
    sub_ok = sub.exists() and sample is not None and _submission_ok(sub, sample)
    grade = mle.grade(cid, sub) if sub.exists() else None
    row = {"key": key, "competition": cid, "output": output, "seconds": round(seconds, 1),
           "ok": bool(code_ok and sub_ok and val is not None and val == val), "val": val, "grade": grade}
    with _exec_lock:
        _exec_cache[key] = row
        EXEC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(EXEC_CACHE, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")
    shutil.rmtree(run_dir / "submission", ignore_errors=True)
    return row


def _better(a, b, lower):
    return a < b if lower else a > b


def solve(h, cid, replica, workdir, progress=None):
    """One attempt at one competition with harness h."""
    cfg = h["config"]
    ctx = context([cid])[cid]
    lower = ctx["lower"]
    description = ctx["obfuscated"] if cfg.get("obfuscate") else ctx["description"]
    rows = cfg["preview_rows"]
    if str(rows) not in ctx["preview"]:
        ctx["preview"][str(rows)] = data_preview(mle.get(cid).public, rows)
    preview = ctx["preview"][str(rows)]
    fill = {"description": description.strip(), "data_preview": preview, "timeout": cfg["exec_timeout"],
            "direction": "lower" if lower else "higher"}
    system = system_prompt(h)
    att = Attempt(cid, replica)
    debug_depth = 0
    for step in range(cfg["steps"]):
        good = [i for i, n in enumerate(att.nodes) if n.ok]
        last = att.nodes[-1] if att.nodes else None
        if last and not last.ok and debug_depth < cfg["max_debug"]:
            stage, parent = "debug", len(att.nodes) - 1
            debug_depth += 1
        elif sum(n.stage == "draft" for n in att.nodes) < cfg["num_drafts"] or not good:
            stage, parent, debug_depth = "draft", None, 0
        else:
            stage, parent, debug_depth = "improve", att.best, 0
        values = dict(fill)
        if parent is not None:
            values.update(code=att.nodes[parent].code, output=att.nodes[parent].output[-1500:],
                          score=att.nodes[parent].val)
        prompt = render(h[stage], values)
        text, pt, ct = llm.chat([{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                                cfg["model"], cfg["temperature"], sample=replica * 100 + step,
                                max_tokens=cfg["max_tokens"])
        att.tokens += pt + ct
        att.calls += 1
        node = Node(step, stage, parent, plan=text.split("```")[0].strip()[:300], code=extract_code(text))
        if node.code:
            r = execute(cid, node.code, Path(workdir) / f"{cid}-r{replica}-s{step}", cfg["exec_timeout"])
            node.output, node.ok, node.val, node.seconds, node.grade = r["output"], r["ok"], r["val"], r["seconds"], r["grade"]
        else:
            node.output = "No ```python block found in the reply."
        att.nodes.append(node)
        if node.ok and (att.best is None or _better(node.val, att.nodes[att.best].val, lower)):
            att.best = step
        if progress:
            progress(f"{cid[:28]:28s} r{replica} step {step} {stage:7s} ok={node.ok} val={node.val}")
    return att


# Offline replay needs the prompt context without the Kaggle data: it is stored once per competition.
CONTEXT = llm.CACHE_DIR / "context.json"


def _terms(comp):
    """Names that identify this competition: used by the leakage critic."""
    terms = set()
    for csv in sorted(comp.public.glob("*.csv"))[:3]:
        with open(csv, encoding="utf-8", errors="replace") as f:
            header = f.readline().strip().split(",")
        terms |= {c.strip('"') for c in header if len(c.strip('"')) >= 3}
    return sorted(terms)


def context(cids):
    """Description, metric direction, previews and identifying terms for each competition (cached)."""
    ctx = json.loads(CONTEXT.read_text(encoding="utf-8")) if CONTEXT.exists() else {}
    missing = [c for c in cids if c not in ctx]
    if missing and os.environ.get("RSI_LLM") != "replay":
        for cid in missing:
            comp = mle.get(cid)
            ctx[cid] = {"lower": comp.lower_is_better, "description": comp.description,
                        "obfuscated": mle.obfuscated_description(cid),
                        "preview": {str(r): data_preview(comp.public, r) for r in (0, 3, 10)},
                        "terms": _terms(comp)}
        CONTEXT.parent.mkdir(parents=True, exist_ok=True)
        CONTEXT.write_text(json.dumps(ctx, indent=1), encoding="utf-8")
    return ctx

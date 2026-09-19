"""Skill packs on disk: reading them, linting them against the task, versioning
them and rolling them back.

A pack is a directory with `SKILL.md` (front matter + body) and sibling files
the harness appends to the prompt. `lint_pack` is the gate every generated or
patched pack passes before a human sees it: front matter, tools.md, the budget
and test rule of the task it was written for, loop / graph sanity, and a dry
boot. `snapshot` / `rollback` are safe inheritance made concrete: every
generation is a directory you can diff and restore.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path

import yaml

from common import recipe

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)   # the block between the two --- lines

PROMPT_FILES = ("tools.md", "schema.json", "loop.json", "recipes.json", "graph.json", "paths.json",
                "memory.schema.json", "memory.json", "eval.md", "policies.md", "task.json", "plan.json",
                "template", "modules", "skill-memory", "working.md", "operators.md", "roles")
IGNORED = ("__pycache__",)

# the guard every AIDE2 operator prompt must carry verbatim (lesson 15)
ANTI_OVERFIT = "Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed."

# the acceptance rule every verifier pack must state verbatim: what it may see, and therefore what it may not
VERIFIER_CONTRACT = ("Contract: the verifier sees only {recipe, val_score, error, profile}; "
                     "it never sees the actor's transcript, the test split or the intent.")


def split_front_matter(text):
    """(front matter dict, body) of any markdown file with a --- block on top; a file without one is ({}, text)."""
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    return (meta if isinstance(meta, dict) else {}), text[match.end():]


def parse_front_matter(text):
    """A SKILL.md's front matter: it must exist and name the skill and when to use it."""
    if not FRONT_MATTER.match(text):
        raise ValueError("SKILL.md has no front matter")
    meta, body = split_front_matter(text)
    if "name" not in meta or "description" not in meta:
        raise ValueError("front matter needs name and description")
    return meta, body


def read_pack(pack_dir):
    """Every file of the pack as {relative path: text}, sorted, so a pack is one dict you can diff."""
    pack_dir = Path(pack_dir)
    files = {}
    for path in sorted(pack_dir.rglob("*")):
        if path.is_file() and not any(part in IGNORED for part in path.parts):
            files[path.relative_to(pack_dir).as_posix()] = path.read_text(encoding="utf-8")
    return files


def write_pack(pack_dir, files):
    pack_dir = Path(pack_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        path = pack_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def checksums(pack_dir):
    return {name: hashlib.sha256(text.encode("utf-8")).hexdigest()[:12] for name, text in read_pack(pack_dir).items()}


def allowed_tools(tools_md):
    """The `- name` bullets under `## Allowed`: the set the harness offers. Everything else is refused."""
    allowed, section = [], None
    for line in tools_md.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
        elif line.startswith("- ") and section == "allowed":
            allowed.append(line[2:].split()[0].strip("`"))
    return allowed


def lint_pack(pack_dir, task):
    """Every reason this pack may not run for this task, as a list of strings. Empty = it may.
    A directory of packs (no SKILL.md at the top, one per subdirectory) is linted pack by pack."""
    pack_dir = Path(pack_dir)
    problems = []
    files = read_pack(pack_dir)
    if "SKILL.md" not in files:
        subs = sorted({name.split("/")[0] for name in files if "/" in name and name.endswith("SKILL.md")})
        if not subs:
            return ["no SKILL.md"]
        for sub in subs:
            problems += [f"{sub}: {p}" for p in lint_pack(pack_dir / sub, task)]
        return problems
    try:
        meta, body = parse_front_matter(files["SKILL.md"])
    except ValueError as e:
        return [str(e)]
    md = meta.get("metadata") or {}
    for key in ("type", "version", "rsi"):
        if key not in md:
            problems.append(f"front matter metadata lacks {key}")
    if "tools.md" not in files:
        problems.append("no tools.md")
        return problems
    allowed = allowed_tools(files["tools.md"])
    if not allowed:
        problems.append("tools.md allows nothing")

    if "schema.json" in files:
        schema = json.loads(files["schema.json"])
        n_fits = schema.get("n_fits")
        if n_fits != task["budget"]["n_fits"]:
            problems.append(f"schema.json n_fits {n_fits} != task budget {task['budget']['n_fits']}")
        if schema.get("test_rule") != task["test_rule"]:
            problems.append("schema.json test_rule differs from the task's")
        if "metric" in schema and schema["metric"] != task["metric"]:   # a curriculum pack names no metric
            problems.append(f"schema.json metric {schema.get('metric')!r} != task metric {task['metric']!r}")
        if not set(schema.get("models", [])) <= set(task["allowed_models"]):
            problems.append("schema.json names a model the task does not allow")
        for rec in schema.get("recipes", []):
            try:
                recipe.validate(rec)
            except ValueError as e:
                problems.append(f"schema.json recipe: {e}")
    if "fit_recipe" in allowed and "schema.json" not in files:
        problems.append("a pack that fits needs schema.json")
    prose = body + "".join(t for n, t in files.items() if n.endswith(".md"))   # SKILL.md and the module files it boots
    if "score_test" in allowed and "after FREEZE" not in prose:
        problems.append("SKILL.md must say score_test runs once, after FREEZE")

    if "loop.json" in files:
        problems += lint_loop(json.loads(files["loop.json"]), task, files)
    if "graph.json" in files:
        from common.graph import lint_graph
        problems += lint_graph(json.loads(files["graph.json"]), json.loads(files.get("paths.json", "[]")), task)
    if "write_card" in allowed and "memory.schema.json" not in files:
        problems.append("a verifier pack needs memory.schema.json")
    if "write_card" in allowed and VERIFIER_CONTRACT not in body:
        problems.append("a verifier pack must state the verifier contract verbatim")
    if "write_card" in allowed and any(t in allowed for t in ("fit_recipe", "score_test", "walk_path")):
        problems.append("a verifier pack may not fit or score: no one grades their own homework")
    if "operators.md" in files:
        for section in files["operators.md"].split("\n## ")[1:]:
            if ANTI_OVERFIT not in section:
                problems.append(f"operator {section.splitlines()[0].strip()!r} lacks the anti-overfitting line")
    has_memory = any(n in files for n in ("memory.schema.json", "memory.json")) or any(n.startswith("skill-memory/") for n in files)
    if md.get("rsi") == "on" and not has_memory and not any(t in allowed for t in ("patch_pack", "write_card", "skill_memory")):
        problems.append("rsi: on without a memory file or a tool that changes one")
    return problems


def lint_loop(loop, task, files):
    problems = []
    if loop.get("kind") != "counted_while":
        problems.append("loop.json kind must be counted_while")
    if loop.get("N") != task["budget"]["n_fits"]:
        problems.append(f"loop.json N {loop.get('N')} != task budget {task['budget']['n_fits']}")
    if not loop.get("error_still_counts", False):
        problems.append("loop.json must count errors")
    exit_steps = loop.get("exit", [])
    if exit_steps[:2] != ["FREEZE", "score_test"]:
        problems.append("loop.json exit must be FREEZE then score_test")
    if "paths.json" in files and len(json.loads(files["paths.json"])) != loop["N"]:
        problems.append(f"paths.json has {len(json.loads(files['paths.json']))} paths for N={loop['N']}")
    if "recipes.json" in files and "paths.json" not in files:
        recipes = json.loads(files["recipes.json"])
        if len(recipes) != loop["N"]:
            problems.append(f"recipes.json has {len(recipes)} recipes for N={loop['N']}")
        for rec in recipes:
            try:
                recipe.validate(rec)
            except ValueError as e:
                problems.append(f"recipes.json: {e}")
    return problems


def snapshot(pack_dir, versions_dir, label):
    """Copy the pack into versions/<label>/ with a checksum manifest. Returns the copy's path."""
    dest = Path(versions_dir) / label
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(pack_dir, dest, ignore=shutil.ignore_patterns(*IGNORED))
    with open(dest / "CHECKSUMS.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(checksums(pack_dir), f, indent=1)
        f.write("\n")
    return dest


def rollback(pack_dir, versions_dir, label):
    """Restore the pack from versions/<label>/: every file of the snapshot lands, extras of the live pack go."""
    src = Path(versions_dir) / label
    if not src.exists():
        raise FileNotFoundError(f"no version {label!r} under {versions_dir}")
    files = {k: v for k, v in read_pack(src).items() if k != "CHECKSUMS.json"}
    pack_dir = Path(pack_dir)
    for path in list(pack_dir.rglob("*")):
        if path.is_file() and not any(part in IGNORED for part in path.parts):
            path.unlink()
    write_pack(pack_dir, files)
    return files


def diff(before, after):
    """A unified diff of two {path: text} dicts, for the human to read at the approval prompt."""
    import difflib

    out = []
    for name in sorted(set(before) | set(after)):
        a, b = before.get(name, ""), after.get(name, "")
        if a != b:
            out += difflib.unified_diff(a.splitlines(), b.splitlines(), f"a/{name}", f"b/{name}", lineterm="", n=1)
    return "\n".join(out)

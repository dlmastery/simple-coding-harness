"""Edits to harness files: the only way an improver may change the agent.

An edit names one file:

    {"file": "skills/validation.md", "action": "write", "content": "...", "why": "..."}
    {"file": "config.json", "action": "set", "key": "steps", "value": 6, "why": "..."}
    {"file": "skills/old.md", "action": "delete", "why": "..."}

`apply` refuses anything that would break the harness's integrity: files
outside the harness, changing the frozen model, or prompt templates that lose
the placeholders the agent fills in. Refused edits are reported, not hidden.
"""

import difflib
import json
import shutil
from pathlib import Path

TEMPLATES = {"draft.md": ["{description}", "{data_preview}"],
             "improve.md": ["{code}", "{output}"],
             "debug.md": ["{code}", "{output}"],
             "system.md": []}
FROZEN_KEYS = {"model"}
CONFIG_LIMITS = {"steps": (1, 12), "num_drafts": (1, 6), "max_debug": (0, 4), "exec_timeout": (30, 900),
                 "preview_rows": (0, 20), "temperature": (0.0, 1.2), "max_tokens": (500, 8000)}


def allowed(rel):
    rel = rel.replace("\\", "/")
    return (rel in TEMPLATES or rel in ("config.json", "memory.md")
            or (rel.startswith("skills/") and rel.endswith(".md") and rel.count("/") == 1 and ".." not in rel))


def check(edit, harness_dir):
    """Return a reason to refuse this edit, or None."""
    rel = edit.get("file", "")
    if not allowed(rel):
        return f"{rel!r} is outside the editable harness"
    action = edit.get("action")
    if rel == "config.json":
        if action != "set":
            return "config.json only accepts set"
        key, value = edit.get("key"), edit.get("value")
        if key in FROZEN_KEYS:
            return f"config key {key!r} is frozen"
        if key in CONFIG_LIMITS:
            lo, hi = CONFIG_LIMITS[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not lo <= value <= hi:
                return f"{key}={value!r} outside [{lo}, {hi}]"
        elif key != "memory":
            return f"unknown config key {key!r}"
        return None
    if action == "delete":
        return "templates cannot be deleted" if rel in TEMPLATES else None
    if action != "write" or not isinstance(edit.get("content"), str):
        return "need action write with string content"
    for ph in TEMPLATES.get(rel, []):
        if ph not in edit["content"]:
            return f"{rel} must keep the placeholder {ph}"
    return None


def apply(harness_dir, edits, out_dir):
    """Copy harness_dir to out_dir and apply the acceptable edits. Returns (applied, refused)."""
    harness_dir, out_dir = Path(harness_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(harness_dir, out_dir)
    applied, refused = [], []
    for e in edits:
        reason = check(e, out_dir)
        if reason:
            refused.append({**e, "refused": reason})
            continue
        path = out_dir / e["file"]
        if e["file"] == "config.json":
            cfg = json.loads(path.read_text(encoding="utf-8"))
            cfg[e["key"]] = e["value"]
            path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        elif e["action"] == "delete":
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(e["content"].rstrip() + "\n", encoding="utf-8")
        applied.append(e)
    return applied, refused


def files(harness_dir):
    d = Path(harness_dir)
    return {p.relative_to(d).as_posix(): p.read_text(encoding="utf-8") for p in sorted(d.rglob("*")) if p.is_file()}


def diff(old_dir, new_dir):
    a, b = files(old_dir), files(new_dir)
    out = []
    for name in sorted(set(a) | set(b)):
        if a.get(name) != b.get(name):
            out += difflib.unified_diff((a.get(name) or "").splitlines(), (b.get(name) or "").splitlines(),
                                        f"a/{name}", f"b/{name}", lineterm="", n=1)
    return "\n".join(out)


def summary(edit):
    if edit["file"] == "config.json":
        return f"config.{edit['key']} = {edit['value']}"
    if edit["action"] == "delete":
        return f"delete {edit['file']}"
    return f"write {edit['file']} ({len(edit['content'])} chars)"

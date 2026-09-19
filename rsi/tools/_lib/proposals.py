"""The human approval cycle on disk: propose -> show -> the user's words -> apply.

A proposal is a file, `runs/<pack>/<task>/proposals/<id>.json`, with the
payload (a whole pack as {path: text}, or a patch as {files: {path: {after}},
recipe}) and a human-readable diff next to it. Nothing lands when it is
written. `apply` needs the user's exact words: a word that says yes lands
the payload, `edit` lands the user's version (`--edited`), anything that
says no is recorded as a rejection and nothing lands. Who approved, and
with which words, is in the trace. There is no default answer: an agent
that does not ask cannot apply.
"""

import json
import re
from difflib import unified_diff
from pathlib import Path

from _lib import packs

YES = ("y", "yes", "approve", "approved", "ok", "okay", "lgtm", "go", "ship", "accept", "accepted", "apply", "land", "sure")
NO = ("n", "no", "reject", "rejected", "nope", "deny", "denied", "stop", "cancel", "decline")
EDIT = ("edit", "edited", "change", "modify")


def classify(words):
    """The user's words -> y / n / edit, by the first word. Anything unclear is a no: nothing lands by default."""
    first = re.sub(r"[^a-z]", "", (words or "").strip().lower().split(" ")[0]) if words and words.strip() else ""
    if first in EDIT:
        return "edit"
    if first in YES:
        return "y"
    if first in NO:
        return "n"
    return "n"


def proposals_dir(root):
    d = Path(root) / "proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def next_id(root, prefix="p"):
    existing = [p.stem for p in proposals_dir(root).glob(f"{prefix}*.json")]
    return f"{prefix}{len(existing) + 1}"


def render(kind, payload, target=None):
    """The text the user reads: every file of a pack, or the unified diff of a patch against the target."""
    out = []
    if kind == "pack":
        if any(packs.VERIFIER_CONTRACT in (t or "") for t in payload.values()):
            out.append(f"### verifier contract (the acceptance rule you are approving)\n{packs.VERIFIER_CONTRACT}\n")
        current = packs.read_pack(target) if target and Path(target).exists() else {}
        for name, text in payload.items():
            if name.endswith("graph.json"):
                g = json.loads(text)
                out.append(f"### {name} as a graph\nnodes: {', '.join(g['nodes'])}\nedges: " + "; ".join(f"{a} -> {b}" for a, b in g["edges"]))
            if name in current and current[name] != text:
                out.append("\n".join(unified_diff(current[name].splitlines(), text.splitlines(), f"a/{name}", f"b/{name}", lineterm="", n=1)))
            else:
                out.append(f"### {name}\n{text.rstrip()}")
    elif kind == "patch":
        for name, change in payload["files"].items():
            before = (change.get("before") or "").splitlines()
            after = (change.get("after") or "").splitlines()
            out.append("\n".join(unified_diff(before, after, f"a/{name}", f"b/{name}", lineterm="", n=1)))
        if payload.get("recipe"):
            out.append(f"(evidence recipe: {json.dumps(payload['recipe'])})")
    else:
        out.append(json.dumps(payload, indent=1))
    return "\n".join(out)


def write(root, kind, payload, summary, target, prefix="p", extra=None):
    pid = next_id(root, prefix)
    diff = render(kind, payload, target)
    record = {"id": pid, "kind": kind, "summary": summary, "target": str(target), "payload": payload, "decision": None,
              "approved_by": None, "words": None, "applied": False, **(extra or {})}
    d = proposals_dir(root)
    save(d / f"{pid}.json", record)
    with open(d / f"{pid}.diff", "w", encoding="utf-8", newline="\n") as f:
        f.write(diff + "\n")
    return record, diff


def save(path, record):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, indent=1)
        f.write("\n")


def load(root, pid):
    path = proposals_dir(root) / f"{pid}.json"
    if not path.exists():
        raise ValueError(f"no proposal {pid!r} under {path.parent}; run propose first and show its diff to the user")
    return path, json.loads(path.read_text(encoding="utf-8"))


def land_pack(target, files):
    import shutil

    target = Path(target)
    if target.exists():
        shutil.rmtree(target)
    packs.write_pack(target, files)
    return packs.checksums(target)


def land_patch(target, versions_dir, patch):
    """Snapshot the target under versions/gen_NNN, then write the patched files. Returns the snapshot label."""
    versions_dir = Path(versions_dir)
    label = f"gen_{len(list(versions_dir.glob('gen_*'))) + 1:03d}" if versions_dir.exists() else "gen_001"
    packs.snapshot(target, versions_dir, label)
    for name, change in patch["files"].items():
        path = Path(target) / name
        if change.get("after") is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(change["after"])
    return label

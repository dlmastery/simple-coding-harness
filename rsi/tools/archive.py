"""archive - the Darwin Goedel Machine lineage: an archive of pack variants with their held-out scores.

    python ../tools/archive.py --pack .claude/skills/dgm-meta --task held-out/02_pool_trees_2.json --target .claude/skills/adult-income \\
        --action add --label gen1-static --held-out held-out
    python ../tools/archive.py --pack ... --task ... --target ... --action parent
    python ../tools/archive.py --pack ... --task ... --target ... --action restore --label gen1-static
    python ../tools/archive.py --pack ... --task ... --target ... --action list

`add` stores the target pack as a variant with its held-out gain: over every
held-out task the target ran (memory arm and control arm, same seed), the
private score of the memory arm's best recipe minus the control arm's,
averaged. `parent` names the variant with the best held-out score, ties to
the older one - never "the latest" by default. `restore` makes a variant the
current pack. The archive lives under runs/<target>/archive/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, packs, tasks  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, target={"required": True, "help": "the actor pack"},
                               action={"required": True, "choices": ["add", "list", "parent", "restore"]},
                               label="the variant's label (add, restore)", parent="the variant this one was rewritten from (add)",
                               held_out={"default": None, "help": "the directory of held-out task files (add)"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "archive")
    target = Run(a.target, a.task, "memory", a.seed, a.run)
    root = target.root.parent / "archive"
    root.mkdir(parents=True, exist_ok=True)
    index_path = root / "archive.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []

    if a.action == "add":
        if not a.label or not a.held_out:
            raise ValueError("add takes --label and --held-out <dir>")
        gains = {}
        for tp in sorted(Path(a.held_out).glob("*.json")):
            task = tasks.load_task(tp)
            mem, ctl = Run(a.target, tp, "memory", a.seed, a.run), Run(a.target, tp, "control", a.seed, a.run)
            mine = [r for r in mem.fit_rows() if r["val_score"] is not None]
            control = [r for r in ctl.fit_rows() if r["val_score"] is not None]
            if not mine or not control:
                continue
            best = max(mine, key=lambda r: r["val_score"])["recipe"]
            base = max(control, key=lambda r: r["val_score"])["recipe"]
            gains[task["name"]] = round(tasks.score_on(task, a.seed, best, "private") - tasks.score_on(task, a.seed, base, "private"), 4)
        if not gains:
            raise ValueError("no held-out task with both arms run: run the target's memory and control arms on the held-out tasks first")
        score = round(sum(gains.values()) / len(gains), 4)
        packs.snapshot(target.pack_dir, root, a.label)
        index = [e for e in index if e["label"] != a.label]
        index.append({"label": a.label, "problem": run.problem, "seed": a.seed, "gains": gains, "held_out": score,
                      "checksums": packs.checksums(target.pack_dir), "parent": a.parent, "policy": packs.policy_line(target.files["SKILL.md"])})
    elif a.action == "restore":
        if a.label not in {e["label"] for e in index}:
            raise ValueError(f"no variant {a.label!r} in the archive")
        packs.rollback(target.pack_dir, root, a.label)
    elif a.action == "parent":
        if not index:
            raise ValueError("the archive is empty; add a variant first")
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
        run.log("archive", action="parent", label=best["label"], latest=index[-1]["label"], size=len(index))
        return {"parent": best["label"], "held_out": best["held_out"], "latest": index[-1]["label"], "is_latest": best["label"] == index[-1]["label"],
                "policies_in_archive": sorted({e.get("policy") for e in index if e.get("policy")})}
    with open(index_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, indent=1)
        f.write("\n")
    run.log("archive", action=a.action, label=a.label, size=len(index))
    return {"action": a.action, "label": a.label, "variants": [{k: e.get(k) for k in ("label", "problem", "held_out", "parent", "policy")} for e in index],
            "checksums": packs.checksums(target.pack_dir) if a.action == "restore" else None}


if __name__ == "__main__":
    cli.main(main)

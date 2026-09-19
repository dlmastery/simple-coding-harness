"""curve - the learning curve: per curriculum problem, the memory arm minus the control arm at the same budget.

    python ../tools/curve.py --pack .claude/skills/adult-income --tasks ../tasks
    python ../tools/curve.py --pack ... --tasks ../tasks/01_adult_income.json,../tasks/02_breast_cancer.json

Reads the scorecards of both arms (memory, control) on every curriculum
task the pack ran, in task order, and writes runs/<pack>/curve.json plus a
table. The headline numbers: gap_val (memory best val - control best val),
gap_test, wasted fits of each arm, cards added / demoted / active. A
problem an arm has not run is listed as missing, not invented.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, tasks  # noqa: E402
from _lib.state import Run  # noqa: E402
from scorecard import card_for  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, tasks={"required": True, "help": "a directory of task.json files, or a comma-separated list"},
                               control={"default": "control", "help": "the name of the control arm (default control)"},
                               ladder={"action": "store_true", "help": "print the ladder of lessons 01-16 with this curve's place"}),
                    task=False)


def task_paths(spec):
    p = Path(spec)
    if p.is_dir():
        return [t for t in sorted(p.glob("*.json")) if tasks.load_task(t)["role"] == "curriculum"]
    return [Path(s.strip()) for s in spec.split(",") if s.strip()]


def row_for(pack, task_path, seed, control_arm, run_override):
    task = tasks.load_task(task_path)
    out = {"problem": task["name"], "title": task["title"], "index": task["index"]}
    cards = {}
    for arm in ("memory", control_arm):
        run = Run(pack, task_path, arm, seed, run_override)
        if not run.opened:
            out[arm] = None
            continue
        cards[arm] = card_for(run)
        out[arm] = cards[arm]
    m, c = cards.get("memory"), cards.get(control_arm)
    if m and c:
        out["gap_val"] = None if m["best_val_score"] is None or c["best_val_score"] is None else round(m["best_val_score"] - c["best_val_score"], 4)
        out["gap_test"] = None if m["test_score"] is None or c["test_score"] is None else round(m["test_score"] - c["test_score"], 4)
        out.update(wasted_memory=m["wasted_fits"], wasted_control=c["wasted_fits"], cards_added=m["cards_added"],
                   cards_demoted=m["cards_demoted"], cards_active=m["cards_active"])
    else:
        out["missing"] = [arm for arm in ("memory", control_arm) if arm not in cards]
    return out


def table(curve):
    lines = [f"{'#':>2} {'problem':<22} {'mem val':>8} {'ctl val':>8} {'gap':>7} {'mem test':>9} {'ctl test':>9} {'wasted m/c':>10} {'cards +/-/act':>13}"]
    for r in curve:
        if r.get("missing"):
            lines.append(f"{r['index']:>2} {r['problem']:<22} missing arm(s): {', '.join(r['missing'])}")
            continue
        m, c = r["memory"], r["control"]
        lines.append(f"{r['index']:>2} {r['problem']:<22} {m['best_val_score']!s:>8} {c['best_val_score']!s:>8} {r['gap_val'] or 0:>+7.4f} "
                     f"{m['test_score']!s:>9} {c['test_score']!s:>9} {r['wasted_memory']:>4}/{r['wasted_control']:<5} "
                     f"{r['cards_added']:>3}/{r['cards_demoted']}/{r['cards_active']}")
    return "\n".join(lines)


def main(argv=None):
    a = PARSER.parse_args(argv)
    paths = task_paths(a.tasks)
    if not paths:
        raise ValueError("no curriculum task found")
    curve = [row_for(a.pack, p, a.seed, a.control, a.run) for p in paths]
    first = Run(a.pack, paths[0], "memory", a.seed, a.run)
    out_path = first.root.parent / "curve.json"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(curve, f, indent=1)
        f.write("\n")
    complete = [r for r in curve if not r.get("missing")]
    summary = {"problems": len(curve), "complete": len(complete),
               "gaps_val": [r["gap_val"] for r in complete], "gaps_test": [r["gap_test"] for r in complete],
               "wasted_memory_total": sum(r["wasted_memory"] for r in complete), "wasted_control_total": sum(r["wasted_control"] for r in complete),
               "never_negative": all((r["gap_val"] or 0) >= 0 for r in complete)}
    return {"curve": curve, "summary": summary, "table": table(curve), "path": str(out_path)}


if __name__ == "__main__":
    cli.main(main)

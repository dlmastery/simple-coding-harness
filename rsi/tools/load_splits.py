"""load_splits - open one arm of a pack on a task: the profile, the metric, the budget.

    python ../tools/load_splits.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
    python ../tools/load_splits.py --pack ... --task ... --arm control --memory off      # the MEMORY_OFF arm

Creates runs/<pack>/<task>/state.json's entry for this arm and seed (a second
call is a no-op: the budget is not reset). Returns the profile a card may
condition on, the split sizes, the number of fits and the applicable cards.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory, tasks  # noqa: E402
from _lib.state import Run  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, memory={"default": "on", "choices": ["on", "off"], "help": "off = the MEMORY_OFF arm: no card is read or written"},
                               freeze_memory={"action": "store_true", "help": "the memory is frozen for this arm (the exam): write_card refuses"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    first = not run.opened
    s = run.open(memory_off_flag=a.memory == "off", memory_frozen=a.freeze_memory)
    parts = tasks.splits(run.task, run.seed)
    if first:
        run.log("boot", pack=run.pack, checksums=s["checksums"], memory_off=run.memory_off, memory_frozen=s["memory_frozen"])
    cards = [] if run.memory_off else memory.applicable(memory.load(run.memory_path), run.profile)
    return {"pack": run.pack, "problem": run.problem, "arm": run.arm, "seed": run.seed, "profile": run.profile,
            "metric": run.task["metric"], "n_fits": s["n_fits"], "fits_used": s["fits_used"], "fits_left": run.left,
            "frozen": s["frozen"], "memory_off": run.memory_off, "memory_frozen": s["memory_frozen"],
            "cards_applicable": cards, "sizes": {k: len(v) for k, v in parts.items() if k in ("train", "val")},
            "state": str(run.state_path)}


if __name__ == "__main__":
    cli.main(main)

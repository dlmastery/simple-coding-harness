"""freeze - FREEZE this arm now: no more fits, whatever is left of the budget; the locked test opens.

    python ../tools/freeze.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json
    python ../tools/freeze.py --pack ... --task ... --memory        # also freeze the memory: write_card refuses from now on

A budget spent to the last fit freezes on its own; this script is for an arm
that stops early (the fits it forfeits are gone, not saved) and for freezing
the memory before the exam.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli  # noqa: E402
from _lib.state import Run  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, memory={"action": "store_true", "help": "freeze memory.json too (the exam)"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    s = run.arm_state
    forfeited = run.left
    run.freeze()
    if a.memory:
        s["memory_frozen"] = True
        run.save()
    run.log("freeze", fits_used=s["fits_used"], forfeited=forfeited, memory_frozen=s["memory_frozen"])
    return {"frozen": True, "fits_used": s["fits_used"], "forfeited": forfeited, "memory_frozen": s["memory_frozen"]}


if __name__ == "__main__":
    cli.main(main)

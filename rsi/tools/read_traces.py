"""read_traces - the fit rows of a pack's log: {recipe, val_score, error} and the profile, nothing else.

    python ../tools/read_traces.py --pack .claude/skills/adult-income --task ../tasks/01_adult_income.json --scope problem
    python ../tools/read_traces.py --pack ... --task ... --scope all              # every problem this pack ran
    python ../tools/read_traces.py --pack ... --task ... --scope problem --of control

This is the verifier's whole input. There is no actor text, no test score
and no intent in a row; the verifier contract is this script's output
shape. `--tally` adds the pairwise wins and losses one field apart and the
cards the verifier's rule would write, so the agent can check its own count.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory  # noqa: E402
from _lib.state import Run  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, scope={"default": "problem", "choices": ["problem", "all"], "help": "this problem (default) or every problem"},
                               of={"default": "memory", "help": "whose fits: the arm (default memory)"},
                               tally={"action": "store_true", "help": "add the pairwise tally and the cards the rule would write"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    if a.scope == "problem":
        raw = run.fit_rows(arm=a.of)
        rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"]} for r in raw]
    else:
        raw = run.all_traces()
        rows = [{"recipe": r["recipe"], "val_score": r["val_score"], "error": r["error"], "problem": r["problem"], "arm": r["arm"], "seed": r["seed"]}
                for r in raw]
    out = {"scope": a.scope, "of": a.of if a.scope == "problem" else "*", "rows": rows, "profile": run.profile, "n": len(rows)}
    if a.tally and a.scope == "problem":
        wins, losses, errors = memory.tally(rows)
        out["tally"] = {"wins": [{"field": f, "value": v, "n": n} for (f, v), n in sorted(wins.items(), key=str)],
                        "losses": [{"field": f, "value": v, "n": n} for (f, v), n in sorted(losses.items(), key=str)],
                        "errored": [{"field": f, "value": v} for f, v in sorted(errors, key=str)]}
        out["cards_by_rule"] = memory.compare(rows, run.profile)
    return out


if __name__ == "__main__":
    cli.main(main)

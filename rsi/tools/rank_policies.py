"""rank_policies - Dream-RSI: replay this problem's log as a simulator and rank search policies with zero fits.

    python ../tools/rank_policies.py --pack .claude/skills/adult-income-meta-dream --task ../tasks/02_breast_cancer.json \\
        --target .claude/skills/adult-income --policies static,obey-memory,random,neighbours-of-top-3,prefer-untried-family

For each named policy: walk its first n_fits picks; a pick the log holds is
answered from the log for free, a pick the log does not hold is `unknown`
(the gym is silent there; an adaptive policy whose next pick depends on an
unknown result stops early). A policy's score is the best logged val among
its picks; at a tie the policy with more unknown picks ranks higher, because
a lap that only revisits the log learns nothing. `saturated` is true when
no policy would visit anything new. The budget counter of the target's arm
is read before and after and reported unchanged: zero fits.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory, packs, policies, recipe  # noqa: E402
from _lib.state import Run, require_tool  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, target={"required": True, "help": "the actor pack whose log and cards are replayed"},
                               policies={"required": True, "help": "policy names, comma-separated"},
                               of={"default": "memory", "help": "whose fits: the arm (default memory)"}))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    require_tool(run.pack_dir, "rank_policies")
    target = Run(a.target, a.task, a.of, a.seed, a.run)
    fits_before = target.arm_state["fits_used"] if target.opened else 0
    rows = target.fit_rows(arm=a.of)
    logged = {recipe.key(r["recipe"]): r["val_score"] for r in rows if r["val_score"] is not None}
    schema = json.loads(target.files["schema.json"])
    static, forbid = schema.get("recipes", recipe.static_list()), schema.get("forbid", [])
    cards = [] if target.memory_off else memory.load(target.memory_path)
    profile = target.profile
    ranking = []
    for name in [p.strip() for p in a.policies.split(",") if p.strip()]:
        fits, tried, unknown = [], [], 0
        try:
            for n in range(1, schema["n_fits"] + 1):
                pick = next((r for r in policies.policy_order(name, static, cards, profile, fits, seed=a.seed, forbid=forbid) if r not in tried), None)
                if pick is None:
                    break
                tried.append(pick)
                if recipe.key(pick) in logged:
                    fits.append(({"recipe": pick}, {"n": n, "val_score": logged[recipe.key(pick)]}))
                else:
                    unknown += 1
        except ValueError as e:
            ranking.append({"policy": name, "error": str(e)})
            continue
        best = max((r["val_score"] for _, r in fits), default=None)
        ranking.append({"policy": name, "best_logged_val": best, "visited": len(fits), "unknown": unknown,
                        "stopped_early": len(fits) + unknown < schema["n_fits"]})
    ranked = [e for e in ranking if "error" not in e]
    ranked.sort(key=lambda e: (-(e["best_logged_val"] or 0), -e["unknown"]))
    fits_after = Run(a.target, a.task, a.of, a.seed, a.run).arm_state["fits_used"] if target.opened else 0
    result = {"ranking": ranked + [e for e in ranking if "error" in e], "winner": ranked[0]["policy"] if ranked else None,
              "fits_spent": fits_after - fits_before, "log_size": len(logged), "saturated": bool(ranked) and all(e["unknown"] == 0 for e in ranked),
              "current_policy": packs.policy_line(target.files["SKILL.md"])}
    run.log("rank_policies", ranking=ranked, fits_spent=result["fits_spent"], log_size=len(logged), winner=result["winner"])
    return result


if __name__ == "__main__":
    cli.main(main)

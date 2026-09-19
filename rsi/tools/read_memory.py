"""read_memory - the cards of a pack's memory.json, and which of them apply to this task's profile.

    python ../tools/read_memory.py --pack .claude/skills/adult-income --task ../tasks/02_breast_cancer.json

With `config.json` `{"memory": "off"}` in the pack, or an arm opened with
`--memory off`, there are no cards: MEMORY_OFF is a line on disk, not a mood.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import cli, memory  # noqa: E402
from _lib.state import Run  # noqa: E402

PARSER = cli.common(cli.parser(__doc__, order="a search policy name (obey-memory, static, random, neighbours-of-top-3, prefer-untried-family, aide-tree): add `next`, the recipes the policy would try next given this arm's fits so far, in order"))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    if run.memory_off:
        out = {"memory_off": True, "cards": [], "applicable": [], "preferred": {}, "profile": run.profile,
               "note": "MEMORY_OFF: no cards this run"}
    else:
        cards = memory.load(run.memory_path)
        applicable = memory.applicable(cards, run.profile)
        preferred = {(k if isinstance(k, str) else f"hyper[{k[1]}]"): v for k, v in memory.preferred(cards, run.profile).items()}
        out = {"memory_off": False, "cards": cards, "applicable": applicable, "preferred": preferred, "profile": run.profile,
               "active": sum(1 for c in cards if memory.active(c))}
    if a.order:
        out["policy"] = a.order
        out["next"] = next_recipes(run, a.order, [] if run.memory_off else memory.load(run.memory_path))
    return out


def next_recipes(run, policy, cards, limit=8):
    """The policy's order over the recipes this arm has not tried, given its fits so far (the policy text of
    SKILL.md as code: `_lib/policies.py`). Zero fits: it reads the state, it does not touch the data."""
    import json

    from _lib import policies, recipe

    schema = json.loads(run.files["schema.json"]) if "schema.json" in run.files else {}
    static = schema.get("recipes", recipe.static_list())
    fits_done = run.arm_state["fits"] if run.opened else []
    fits = [({"recipe": f["recipe"]}, {"n": f["n"], "val_score": f["val_score"]}) for f in fits_done]
    tried = [f["recipe"] for f in fits_done]
    order = policies.policy_order(policy, static, cards, run.profile, fits, seed=run.seed, forbid=schema.get("forbid", []))
    return [r for r in order if r not in tried][:limit]


if __name__ == "__main__":
    cli.main(main)

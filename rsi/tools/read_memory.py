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

PARSER = cli.common(cli.parser(__doc__))


def main(argv=None):
    a = PARSER.parse_args(argv)
    run = Run(a.pack, a.task, a.arm, a.seed, a.run)
    if run.memory_off:
        return {"memory_off": True, "cards": [], "applicable": [], "preferred": {}, "profile": run.profile,
                "note": "MEMORY_OFF: no cards this run"}
    cards = memory.load(run.memory_path)
    applicable = memory.applicable(cards, run.profile)
    preferred = {(k if isinstance(k, str) else f"hyper[{k[1]}]"): v for k, v in memory.preferred(cards, run.profile).items()}
    return {"memory_off": False, "cards": cards, "applicable": applicable, "preferred": preferred, "profile": run.profile,
            "active": sum(1 for c in cards if memory.active(c))}


if __name__ == "__main__":
    cli.main(main)

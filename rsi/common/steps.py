"""What every step's run.py and test_step.py share: a working copy of a pack
(the pack in `skills/` stays pristine; the copy under `runs/` is the one that
boots and learns), the step's task, and the two lines that print a scorecard.
"""

import json
import shutil
from pathlib import Path

from common import tasks


def workspace(step_dir, *names, into=None, fresh=True):
    """Copy skills/<name> for each name into runs/work/ (or `into`) and return the copies' paths."""
    step_dir = Path(step_dir)
    root = Path(into) if into else step_dir / "runs" / "work"
    if fresh and root.exists():
        shutil.rmtree(root)
    out = []
    for name in names:
        dest = root / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(step_dir / "skills" / name, dest)
        out.append(dest)
    return out if len(out) > 1 else out[0]


def step_task(step_dir, default="adult_income"):
    """The step's own task.json when it ships one, else the named curriculum problem."""
    own = Path(step_dir) / "task.json"
    return tasks.load_task(own) if own.exists() else tasks.load_task(default)


def show(card):
    print(json.dumps(card, indent=1))


def brief(card):
    return (f"{card['problem']} [{card['arm']}] fits {card['fits_used']}/{card['n_fits']} wasted {card['wasted_fits']} "
            f"best val {card['best_val_score']} test {card['test_score']} recipe {json.dumps(card['best_recipe'])}")

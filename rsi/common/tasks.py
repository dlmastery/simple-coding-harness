"""The curriculum: one task.json per problem under rsi/tasks/, validated against
task.schema.json, each turned into a frame, a profile and a four-way split.

A task says what to improve (target, metric), how much may be spent (budget),
what may be tried (allowed models), the locked-test rule and the profile keys a
card may condition on. Nothing downstream may widen it: `lint_pack` compares
every pack against the task it was written for.

`fit_for` is the one place a fit happens for a task. It caches by (task, seed,
recipe) because a fit is deterministic: two arms that try the same recipe get
the same number, and the budget counts the *calls*, not the cache misses.
"""

import json
from functools import lru_cache
from pathlib import Path

import jsonschema

from common import data, recipe, synth

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent / "tasks"
TASK_SCHEMA = json.loads((HERE / "task.schema.json").read_text(encoding="utf-8"))


def validate_task(task):
    """The task against task.schema.json; raises jsonschema.ValidationError with the offending path."""
    jsonschema.validate(task, TASK_SCHEMA)
    return task


def load_task(name_or_path):
    path = Path(name_or_path)
    if not path.exists():   # a bare name: the file under rsi/tasks/ whose name ends with it
        path = next(iter(sorted(TASK_DIR.glob(f"*_{name_or_path}.json")) + sorted(TASK_DIR.glob(f"{name_or_path}.json"))), None)
        if path is None:
            raise FileNotFoundError(f"no task named {name_or_path!r} under {TASK_DIR}")
    return validate_task(json.loads(path.read_text(encoding="utf-8")))


def all_tasks(task_dir=TASK_DIR):
    return sorted((load_task(p) for p in Path(task_dir).glob("*.json")), key=lambda t: t["index"])


def curriculum(task_dir=TASK_DIR):
    return [t for t in all_tasks(task_dir) if t["role"] == "curriculum"]


def exam(task_dir=TASK_DIR):
    return next(t for t in all_tasks(task_dir) if t["role"] == "exam")


def synth_task(name, index, role="curriculum", **source):
    """A synthetic task built in code, for the tests: same schema, no file."""
    return validate_task({
        "name": name, "index": index, "title": f"synthetic {name}", "source": {"kind": "synth", **source},
        "target": "target", "metric": "roc_auc_ovr_macro" if source.get("n_classes", 2) > 2 else "roc_auc",
        "budget": {"n_fits": 24, "per": "arm"}, "allowed_models": ["logreg", "rf", "hgb"],
        "test_rule": {"scores": 1, "after": "FREEZE"}, "profile_keys": list(data.PROFILE_KEYS), "role": role,
    })


def test_curriculum():
    """Six small synthetic problems and an exam: the offline curriculum every test runs in seconds, shaped
    like the real one (trees, line, trees multiclass, line multiclass, line, trees; the exam is trees):
    experience must survive a flip of which model wins, not just repeat itself."""
    return [
        synth_task("t1_trees_cat", 1, n=500, seed=101, shift=0, imbalance=0.2),
        synth_task("t2_line_small", 2, n=400, seed=102, shift=1, imbalance=0.4),
        synth_task("t3_trees_multi", 3, n=500, seed=103, shift=0, imbalance=0.3, n_classes=3),
        synth_task("t4_line_multi", 4, n=500, seed=104, shift=1, imbalance=0.3, n_classes=3),
        synth_task("t5_line_balanced", 5, n=500, seed=105, shift=1, imbalance=0.4),
        synth_task("t6_trees_imbalanced", 6, n=450, seed=106, shift=0, imbalance=0.15),
    ], synth_task("t7_exam", 7, role="exam", n=600, seed=107, shift=0, imbalance=0.2)


@lru_cache(maxsize=None)
def _frame(source_key):
    source = json.loads(source_key)
    if source["kind"] == "adult":
        return data.load_adult()
    if source["kind"] == "sklearn":
        return data.load_sklearn(source["name"])
    args = {k: v for k, v in source.items() if k != "kind"}
    return synth.make_table(**args)


def frame(task):
    return _frame(json.dumps(task["source"], sort_keys=True))


def profile(task):
    return data.profile(frame(task))


def splits(task, seed=0):
    return data.split_frame(frame(task), seed)


_FITS = {}


def fit_for(task, seed, rec):
    """Fit one recipe on the task's train split and score it on val. Cached: deterministic, so a repeat is free."""
    k = (json.dumps(task["source"], sort_keys=True), task["metric"], seed, recipe.key(rec))   # the table, not its name
    if k not in _FITS:
        parts = splits(task, seed)
        _FITS[k] = recipe.fit(rec, parts["train"], parts["val"], task["metric"])
    return _FITS[k]


def score_on(task, seed, rec, part):
    """The recipe's fitted pipeline scored on one other split: `test` for the locked test, `private` for the gate."""
    fitted = fit_for(task, seed, rec)
    if fitted["pipeline"] is None:
        return None
    return round(recipe.score(fitted["pipeline"], splits(task, seed)[part], task["metric"]), 4)

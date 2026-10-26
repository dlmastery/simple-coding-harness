"""No-fit construction, policy, role and final-boundary checks before reserved-task search."""
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor

ROOT = Path(__file__).resolve().parents[3]
work = ROOT.parent / "rsi-work-2026-09-22-tabular-comparison"
output = work / "preflight"
output.mkdir(exist_ok=False)
shutil.copyfile(Path(__file__), output / Path(__file__).name)
sys.path.insert(0, str(work / "source"))
from study_engine import build_recipe
from study_policy import ARMS, PREFIX, load_roles, make_plan, memory_order

checks = []


def require(name, condition):
    checks.append(dict(check=name, passed=bool(condition)))
    pd.DataFrame(checks).to_csv(output / "CHECKS.csv", index=False)
    if not condition:
        raise AssertionError(name)


experience = pd.read_csv(work / "memory/EXPERIENCE.csv")
for kind in ("classification", "regression"):
    schema = pd.DataFrame([
        dict(column="x", role="feature", kind="numeric"),
        dict(column="category", role="feature", kind="categorical"),
        dict(column="target", role="target", kind="categorical" if kind == "classification" else "numeric")])
    for template in sorted(experience[experience.kind == kind].candidate.unique()):
        for factor in ([1.] if "median" in template else [1., .3, 3.]):
            model = clone(build_recipe(schema, kind, template, factor))
            model._validate_params()
            pipeline = model.regressor if isinstance(model, TransformedTargetRegressor) else model
            pipeline.named_steps["model"]._validate_params()
            require(f"construct/{kind}/{template}/{factor}", not hasattr(pipeline.named_steps["prepare"], "transformers_"))
    for arm in ARMS:
        plans, roles, _ = make_plan(arm, 123, kind, [], experience, work / "source/roles")
        require(f"{kind}/{arm}/common_prefix", [p["template"] for p in plans] == PREFIX[kind] and len(plans) == 4)
        # Explicitly invented policy-only state, never counted as measured ML.
        history = [dict(step=i+1, template=p["template"], factor=1., status="success", train_loss=.1, selection_loss=.4-i*.02) for i,p in enumerate(plans)]
        next_plans, roles, _ = make_plan(arm, 123, kind, history, experience, work / "source/roles")
        require(f"{kind}/{arm}/allocation", len(next_plans) == (2 if arm in {"parent", "harness", "updater"} else 4))
        require(f"{kind}/{arm}/bounded", all(.05 <= p["factor"] <= 20 for p in next_plans))
        if arm in {"parent", "harness", "updater"}:
            require(f"{kind}/{arm}/roles_read", len(roles) == 5 and all(len(r["sha256"]) == 64 for r in roles))
            require(f"{kind}/{arm}/parent", all(p["parent_step"] == 4 for p in next_plans))
            history.extend(dict(step=5+i, **p, status="success", train_loss=.1, selection_loss=.2+i*.1) for i,p in enumerate(next_plans))
            later, later_roles, _ = make_plan(arm, 123, kind, history, experience, work / "source/roles")
            require(f"{kind}/{arm}/later_use", len(later) == 2 and all(p["parent_step"] == 5 for p in later) and roles == later_roles)
        for p in next_plans:
            clone(build_recipe(schema, kind, p["template"], p["factor"]))
            require(f"{kind}/{arm}/new_construct/{p['template']}/{p['factor']}", True)
bad = output / "invalid-roles"
shutil.copytree(work / "source/roles", bad)
path = bad / "v1/Evolver.md"
path.write_text(path.read_text().replace("selection-loss-then-earlier", "training-loss"))
try:
    load_roles(bad, "v1")
except ValueError:
    refused = True
else:
    refused = False
require("changed_external_rule_refused", refused)
command = [sys.executable, str(work / "source/study_worker.py"), "--phase", "search", "--task", "unused",
           "--builder", "unused", "--kind", "regression", "--output", str(output), "--final-file", "forbidden.csv"]
result = subprocess.run(command, capture_output=True, text=True, timeout=30)
(output / "FINAL-BOUNDARY-REFUSAL.txt").write_text(result.stdout+result.stderr)
require("search_final_argument_refused_before_input", result.returncode != 0 and "Final rows are permitted only" in result.stderr)
(output / "README.md").write_text(f"# No-fit preflight\n\n{len(checks)} checks pass. Model objects were constructed and cloned, never fitted. "
    "Policy checks use explicitly invented loss values. One worker refusal occurred before reading inputs or fitting. "
    "A copied invalid role fixture was refused. Frozen study source and data remain unchanged.\n")
print(f"{len(checks)} no-fit preflight checks passed")

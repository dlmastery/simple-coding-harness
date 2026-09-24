"""Agent-proposed child rule: preserve quadratic and add a new smooth basis."""
import ast
from pathlib import Path


def read_constants(path):
    result = {}
    for item in ast.parse(Path(path).read_text(encoding="utf-8")).body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
            if item.targets[0].id in ("FAMILY", "TRANSFORM", "STRENGTH", "STAGE"):
                result[item.targets[0].id] = ast.literal_eval(item.value)
    return result


def propose(workspace, is_root, root_count):
    workspace = Path(workspace)
    old = read_constants(workspace / "candidate.py")
    if is_root:
        family = ("linear", "boost", "extra", "kernel")[root_count % 4]
        transform, strength, stage = "raw", 1., 0
        reason = "Use the same independent model-family draft as the parent harness."
    else:
        family, stage = old["FAMILY"], old["STAGE"] + 1
        transform, strength = old["TRANSFORM"], old["STRENGTH"]
        if stage == 1:
            transform = "pairwise"
            reason = "Use the same inherited pairwise-feature proposal as the parent."
        elif stage == 2:
            strength = .1 if family in ("linear", "kernel") else 3.
            if family == "linear":
                transform = "quadratic"
                reason = "Test the parent's quadratic linear candidate one position earlier."
            else:
                reason = "Use the parent's regularization or tree-size change."
        elif stage == 3:
            transform = "quadratic-splines" if family == "linear" else "quadratic"
            reason = ("Add a training-fitted smooth basis to the inherited quadratic linear pipeline."
                      if family == "linear" else "Use the parent's quadratic-feature proposal.")
        else:
            strength = min(100., max(.01, strength * (3. if stage % 2 == 0 else .5)))
            reason = "Continue the same bounded local parameter refinement."
    code = ("from engine import build as build_pipeline\n\n"
            f"FAMILY = {family!r}\nTRANSFORM = {transform!r}\nSTRENGTH = {strength!r}\nSTAGE = {stage}\n\n"
            "def build(kind, seed):\n"
            "    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)\n")
    (workspace / "candidate.py").write_text(code, encoding="utf-8", newline="\n")
    (workspace / "CHANGE.md").write_text(
        f"# Candidate change\n\n{reason}\n\nInherited constants: {old!r}\n"
        f"Result: family={family}; transform={transform}; strength={strength}; stage={stage}.\n",
        encoding="utf-8", newline="\n")

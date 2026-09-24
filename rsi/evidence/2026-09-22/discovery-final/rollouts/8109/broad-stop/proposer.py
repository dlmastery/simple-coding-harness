"""Frozen, inspectable local proposer; this is not an LLM discovery agent.

The exploration policy controls which saved workspace receives the next edit.
"""
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
        reason = "Start an independent conventional model family."
    else:
        family, stage = old["FAMILY"], old["STAGE"] + 1
        transform, strength = old["TRANSFORM"], old["STRENGTH"]
        if stage == 1:
            transform = "pairwise"
            reason = "Test pairwise interactions while retaining the inherited family and strength."
        elif stage == 2:
            strength = .1 if family in ("linear", "kernel") else 3.
            reason = "Change one regularization or tree-size parameter in the inherited pipeline."
        elif stage == 3:
            transform = "quadratic"
            reason = "Extend the inherited feature operator to include squared terms."
        else:
            strength = min(100., max(.01, strength * (3. if stage % 2 == 0 else .5)))
            reason = "Continue bounded local parameter refinement from the saved candidate."
    code = ("from engine import build as build_pipeline\n\n"
            f"FAMILY = {family!r}\nTRANSFORM = {transform!r}\nSTRENGTH = {strength!r}\nSTAGE = {stage}\n\n"
            "def build(kind, seed):\n"
            "    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)\n")
    (workspace / "candidate.py").write_text(code, encoding="utf-8", newline="\n")
    (workspace / "CHANGE.md").write_text(
        f"# Candidate change\n\n{reason}\n\nInherited constants: {old!r}\n"
        f"Result: family={family}; transform={transform}; strength={strength}; stage={stage}.\n",
        encoding="utf-8", newline="\n")

"""Author walkthrough from a clean clone and separate learner workspace.

This driver retains actual commands and artifacts. It does not invent learner
responses or create a fresh coding-agent context. Python children use 60s limits.
"""
import argparse
import csv
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    python = Path(sys.executable)
    tool = repo / "rsi/tools/lab.py"
    checker = repo / "rsi/tools/check_result.py"
    commands = []

    def execute(label, script, arguments, expected=0):
        command = [str(python), str(script), *map(str, arguments)]
        started = time.perf_counter()
        try:
            result = subprocess.run(command, cwd=repo, capture_output=True, text=True,
                                    encoding="utf-8", timeout=60)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = 124, str(error.stdout or ""), str(error.stderr or "")
        elapsed = time.perf_counter() - started
        log = out / "commands" / f"{len(commands)+1:03d}-{label}.md"
        save(log, f"# {label}\n\nCommand arguments: {command!r}\n\nExit: {code}; expected: {expected}; wall seconds: {elapsed:.6f}.\n\nStandard output:\n\n```text\n{stdout}\n```\n\nStandard error:\n\n```text\n{stderr}\n```\n")
        commands.append((label, code, expected, elapsed))
        save(out / "COMMANDS.md", "# Actual child commands\n\n| Action | Exit | Expected | Wall seconds |\n|---|---:|---:|---:|\n" + "\n".join(f"| {a} | {b} | {c} | {d:.6f} |" for a,b,c,d in commands) + "\n")
        if code != expected:
            save(out / "PROGRESS.md", f"# Stopped on unexpected result\n\nAction: {label}; exit {code}, expected {expected}. Preserve all artifacts and inspect its command log.\n")
            raise RuntimeError(f"{label}: exit {code}, expected {expected}; see {log}")
        return stdout

    def fit(lab_id, model="constant", features="calendar", policy=None):
        work = out / lab_id
        arguments = ["run", "--task", "bike", "--workspace", work, "--model", model,
                     "--features", features, "--seed", "17", "--hypothesis",
                     f"Test {model} with {features} under the unchanged bike task."]
        if policy:
            arguments += ["--policy", policy]
        execute(f"{lab_id}-{model}-{features}", tool, arguments)
        candidate = work / rows(work / "trials.csv")[-1]["candidate"]
        execute(f"{lab_id}-check-{candidate.name}", checker, [candidate, "--report", candidate / "CHECK.md"])
        return candidate

    def progress(lab_id, statement):
        save(out / lab_id / "PROGRESS.md", f"# Author walkthrough: {lab_id}\n\n{statement}\n\nPrediction, quiz, and teach-back: unattempted; no live learner. Agent context: shared author context.\n")

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    save(out / "SOURCE.md", f"# Source boundary\n\nClone: {repo}\nCommit: {commit}\nPython: {platform.python_version()}\nDriver SHA-256: {digest(Path(__file__))}\n\nFresh files and Python environment; same authoring-agent context.\n")
    freeze = subprocess.check_output([str(python), "-m", "pip", "freeze"], text=True) if subprocess.run([str(python), "-m", "pip", "--version"], capture_output=True).returncode == 0 else "Environment created by uv; see package-versions.csv.\n"
    save(out / "ENVIRONMENT.txt", freeze)
    from importlib.metadata import distributions
    save(out / "package-versions.csv", "package,version\n" + "\n".join(sorted(f"{d.metadata['Name']},{d.version}" for d in distributions())) + "\n")
    task = """# Bike prediction task

One prediction estimates total rentals in one recorded hour. Target: cnt,
measured in rentals per hour. Use calendar fields for the first baseline.
Observed weather is available for later retrospective exercises, not evidence
of a day-ahead forecast. Exclude casual, registered, instant, and the raw target.
Use MAE; smaller is better. Train on 2011, select on the first half of 2012,
and reserve the second half for one final evaluation of a frozen recipe.
Fit transformations only on training data. The public source is UCI Bike
Sharing with repository-pinned attribution and checksums. This local split is
visible to the coding agent and is not a secret evaluation service.
"""
    save(out / "00-01/TASK.md", task)
    with (repo / "rsi/examples/bike-demand/source/hour.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        sample = [next(reader) for _ in range(3)]
    assert all(int(r["casual"]) + int(r["registered"]) == int(r["cnt"]) for r in sample)
    save(out / "00-01/ROW-EXPLANATION.md", "# Three actual source rows\n\n" + "\n".join(f"- {r['dteday']} hour {r['hr']}: {r['casual']} casual + {r['registered']} registered = {r['cnt']} total rentals." for r in sample) + "\n\nThe component counts explain the total, but make invalid prediction inputs for this task.\n")
    progress("00-01", "Task framed and three source rows inspected. No fit.")
    execute("00-02-inspect", tool, ["inspect", "--task", "bike", "--workspace", out / "00-02"])
    assert (out / "00-02/data-overview.png").read_bytes().startswith(b"\x89PNG")
    save(out / "00-02/CAPABILITIES.md", f"# Executed capabilities\n\nRead pinned source, wrote separate files, installed the four documented dependencies, ran Python {platform.python_version()}, and created a PNG and data report. See the package record. Image rendering still needs visual inspection. No native other-agent integration or GPU was tested.\n")
    progress("00-02", "One data inspection completed. No model fits.")
    baseline = fit("00-03")
    predicted = rows(baseline / "predictions.csv")
    errors = [abs(float(r["actual"])-float(r["predicted"])) for r in predicted]
    save(out / "00-04/HAND-CHECK.md", "# Check the arithmetic\n\n" + "\n".join(f"- Row {r['source_row']}: |{r['actual']} - {r['predicted']}| = {abs(float(r['actual'])-float(r['predicted'])):.6f}." for r in predicted[:3]) + f"\n\nMean over all {len(errors)} selection rows: {sum(errors)/len(errors):.9f}. The three displayed rows explain the calculation; they do not replace the complete metric.\n")
    process = """# Fixed baseline process

1. Read TASK.md and the pinned bike data card. Keep the source intact.
2. Inspect the data and chronological partitions; retain the report and plot.
3. Fit the training-median baseline with calendar inputs and seed 17 once.
4. Recompute MAE from the expected selection rows and saved predictions.
5. Preserve predictions, result, checks, versions, costs, and this trace. Stop.
"""
    save(out / "01-01/PROCESS.md", process)
    save(out / "01-01/TASK.md", task)
    execute("01-02-inspect", tool, ["inspect", "--task", "bike", "--workspace", out / "01-02"])
    repeated = fit("01-02")
    assert digest(repeated / "predictions.csv") == digest(baseline / "predictions.csv")
    save(out / "01-02/REPEATABILITY.md", f"# Observed repeatability\n\nThe fresh run and 00-03 prediction files have identical SHA-256 {digest(baseline / 'predictions.csv')}. Fit and command wall times remain separately recorded. The procedure did not learn.\n")
    skill = """# Baseline skill, version 1

Use for one reproducible bike baseline. Read TASK.md, the pinned data card,
and the course tool instructions. Inspect data, then run exactly one
constant/calendar candidate with seed 17. Recompute the selection metric from
its expected row identities and source targets. Keep failures and stop after
one fit. Do not change the metric, split, target, or data. Refuse leaked inputs.
Write progress and report actual files. The host agent supplies execution;
this Markdown file is not an access-control boundary.
"""
    policy = out / "01-03/BASELINE-SKILL.md"
    save(policy, skill)
    save(out / "01-03/TASK.md", task)
    # The author read and chose this generated procedure; the child tool snapshots it.
    assert "exactly one" in policy.read_text(encoding="utf-8")
    skill_run = fit("01-03", policy=policy)
    assert digest(skill_run / "predictions.csv") == digest(baseline / "predictions.csv")
    save(out / "01-03/DECISION.md", "# Applied instruction\n\nThe retained skill specifies constant/calendar, seed 17, and one fit. Those instructions determined this run. The result checker then checked the actual output. No search or skill update occurred.\n")
    altered = out / "01-04/altered-copy"
    shutil.copytree(out / "01-03", altered)
    faulty = altered / "trial-001/predictions.csv"
    lines = faulty.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[0] = "0"
    lines[1] = ",".join(cells)
    save(faulty, "\n".join(lines)+"\n")
    execute("01-04-valid", checker, [skill_run, "--report", out / "01-04/VALID.md"])
    execute("01-04-wrong-row", checker, [altered / "trial-001", "--report", out / "01-04/REFUSAL.md"], expected=1)
    save(out / "01-04/CHECK-REPORT.md", "# Identity check\n\nThe genuine output passed. A labelled copy replacing the first selection row ID with training row 0 failed. The original predictions remain unchanged. This check shares the author's file access; it establishes no secrecy.\n")
    save(out / "01-05/HANDOFF.md", f"# File-based handoff\n\nRead ../01-03/BASELINE-SKILL.md (SHA-256 {digest(policy)}) and ../01-03/TASK.md. Use the pinned clone's Python environment. Run one candidate in this new workspace and check it. No expected metric is supplied. This author walkthrough uses another process in the same agent context.\n")
    reused = fit("01-05", policy=policy)
    assert digest(reused / "predictions.csv") == digest(baseline / "predictions.csv")
    progress("01-05", "File-based procedure reused in a new Python process; genuine fresh-agent context remains untested.")
    for lab_id, recipes in [
        ("02-01", [("constant","calendar"),("linear","calendar")]),
        ("02-02", [("constant","calendar"),("linear","calendar"),("tree","calendar")]),
        ("02-03", [("linear","calendar"),("linear","all")]),
    ]:
        save(out / lab_id / "PLAN.md", f"# Prespecified comparison\n\nRecipes: {recipes}. Seed 17. Maximum fits: {len(recipes)}. Same task, split, and MAE. Keep earlier candidate on a tie. No final-set selection.\n")
        for model, features in recipes:
            fit(lab_id, model, features)
        execute(f"{lab_id}-compare", tool, ["compare", "--workspace", out / lab_id])
        progress(lab_id, f"Completed exactly {len(recipes)} planned fits and checked all outputs. The shared tool advertises 12 attempts; the author obeyed the smaller lesson budget. See the generated controller in 02-04 for enforced smaller limits.")
    controller = out / "02-04/controller.py"
    controller.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("journey-controller.py"), controller)

    def controlled(lab_id, limit, model, expected=0, action="run", candidate=None):
        arguments = [action, "--repo", repo, "--workspace", out / lab_id, "--limit", limit,
                     "--model", model, "--features", "calendar", "--hypothesis", "Bounded recipe comparison after the saved checkpoint."]
        if candidate:
            arguments += ["--candidate", candidate]
        execute(f"{lab_id}-{action}-{model}-{len(commands)}", controller, arguments, expected)

    controlled("02-04", 2, "linear")
    controlled("02-04", 2, "tree")
    controlled("02-04", 2, "linear", 1)
    controlled("02-04", 2, "forest", 1)
    assert len(rows(out / "02-04/trials.csv")) == 2
    controlled("02-05", 3, "constant")
    checkpoint_hash = digest(out / "02-05/trial-001/predictions.csv")
    progress("02-05", "Checkpoint: trial-001 complete; one attempt consumed, two remain. No .running lock remains. Next: linear/calendar, then tree/calendar in new processes.")
    shutil.copyfile(out / "02-05/PROGRESS.md", out / "02-05/CHECKPOINT-1.md")
    assert not (out / "02-05/.running").exists()
    assert len(rows(out / "02-05/trials.csv")) == 1
    controlled("02-05", 3, "linear")
    controlled("02-05", 3, "tree")
    controlled("02-05", 3, "forest", 1)
    controlled("02-05", 3, "constant", action="compare")
    assert digest(out / "02-05/trial-001/predictions.csv") == checkpoint_hash
    assert [r["candidate"] for r in rows(out / "02-05/trials.csv")] == ["trial-001", "trial-002", "trial-003"]
    progress("02-05", "Resumed across child processes. Three attempts total; the original prediction hash survived. The fourth request was refused. No new agent context or forced process interruption was tested.")
    save(out / "FOUNDATION-RESULT.md", f"# Foundation result\n\nExecuted {len(commands)} recorded child commands. All expected outcomes matched, including three controller refusals and the row-identity rejection. Sixteen model fits ran across separate lesson workspaces; no final evaluation ran. No learner answers were collected.\n\nThe smaller lesson budgets were followed by the maintainer in early steps and enforced by generated code in 02-04/02-05. Fresh-context and interrupted-process recovery remain separate tests.\n")
    save(out / "PROGRESS.md", "# Clean journey progress\n\nFoundation stage complete. Next: graph and domain checks using these actual artifacts, then generated harnesses and a bounded improver comparison. Preserve every completed workspace. Learner assessments remain unattempted.\n")
    print(f"Foundation complete: {len(commands)} child commands, evidence at {out}.")


if __name__ == "__main__":
    main()

"""Generate and execute two complete teaching packages from saved prose briefs."""
import argparse
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.workspace.resolve()
    if any((out / name).exists() for name in ["06-01", "06-02", "06-03", "06-04", "06-05", "06-06"]):
        raise RuntimeError("Preserve the existing harness stage.")
    builder = repo / "rsi/skills/build-ml-harness/SKILL.md"
    builder_hash = digest(builder)
    source = (out / "02-04/controller.py").read_text(encoding="utf-8")
    calls = []
    def execute(label, script, arguments, expected=0):
        command = [sys.executable,str(script),*map(str,arguments)]
        start = time.perf_counter()
        result = subprocess.run(command,cwd=repo,capture_output=True,text=True,encoding="utf-8",timeout=60)
        elapsed = time.perf_counter()-start
        save(out / "harness-commands" / f"{len(calls)+1:02}-{label}.md",f"# {label}\n\nArguments: {command!r}\n\nExit: {result.returncode}; expected {expected}; wall seconds: {elapsed:.6f}.\n\n```text\n{result.stdout}\n{result.stderr}\n```\n")
        calls.append((label,result.returncode,expected,elapsed))
        save(out / "HARNESS-EXECUTION.md","# Harness execution\n\n| Action | Exit | Expected | Wall seconds |\n|---|---:|---:|---:|\n" + "\n".join(f"| {a} | {b} | {c} | {d:.6f} |" for a,b,c,d in calls)+"\n")
        assert result.returncode == expected, f"Unexpected result: {label}"
    for task,folder in [("bike","06-02"),("wine","06-05")]:
        specification = ("Estimate hourly cnt with calendar inputs, optionally observed weather. This is retrospective, not a day-ahead forecast. Exclude target components casual and registered. Train on 2011, select on 2012-H1, reserve 2012-H2. Use MAE; lower is better. Baseline: training median." if task == "bike" else
                         "Classify red-wine quality >= 7. Use physicochemical inputs only. Keep identical input vectors together using the pinned wine-v1 hash split. Fit preprocessing on training rows. Use balanced accuracy and both class recalls; larger balanced accuracy is better. Baseline: majority class; compare balanced logistic regression.")
        brief = f"# {task.title()} harness brief\n\n{specification}\n\nUse the repository-pinned UCI data and attribution. Allow two admitted attempts, including failures; refuse a third. Refuse changed task, metric, or split. Keep candidates, predictions, checks, failures, and measured costs. Default to CPU with sequential commands capped at 60 seconds. The data and evaluator are visible to the host agent. Students type ordinary language; the coding agent supplies code.\n"
        brief_path = out / ("06-01/HARNESS-BRIEF.md" if task == "bike" else "06-05/HARNESS-BRIEF.md")
        save(brief_path,brief)
        package = out / folder / "package"
        code = source.replace('choices=["bike", "wine"], default="bike"',f'choices=["{task}"], default="{task}"')
        code = code.replace('parser.add_argument("--limit", type=int, required=True)', 'parser.add_argument("--limit", type=int, choices=[2], default=2)')
        if task == "wine":
            code = code.replace('parser.add_argument("--features", default="calendar")','parser.add_argument("--features", default="all")')
        save(package / "run.py",code)
        save(package / "TASK.md",brief)
        save(package / "README.md",f"# Generated {task} harness\n\nAsk your coding agent to read TASK.md, WORKFLOW.md, and RECOVERY.md, locate the recorded source clone, and run one declared recipe in a new output folder. The agent handles Python setup and commands. The run entry accepts run, compare, or final, plus repository and workspace paths. Task {task} and a two-attempt limit are fixed in generated code.\n\nThis package imports the course's shared tools; it is not a standalone replacement for the repository. Its tests are replayed by the retained harness-stage driver. See ACCEPTANCE.md.\n")
        save(package / "WORKFLOW.md","# Generated workflow\n\nRead the task and source data card → inspect data and partition roles → validate allowed inputs → fit one baseline → check predicted row identities and recompute the metric → consider the declared candidate if budget remains → compare checked candidates → report and stop. Invalid task arguments fail at entry. Invalid feature requests fail before model fitting and consume an admitted attempt. Duplicate and exhausted-budget requests do not add a fit. Final evaluation is a separate explicit action.\n")
        save(package / "RECOVERY.md","# Stop and recover\n\nThe agent imposes a 60-second command limit. Preserve a timeout or nonzero result. Before resume, inspect requests.csv, trials.csv, CONTROLLER-CONTRACT.md, and any .running process. Do not remove a live lock or reset attempts. An interrupted trial needs the shared tool's documented recovery. A source or task change needs a new experiment. Final evaluation closes the workspace. Keep the last accepted result and failures.\n")
        save(package / "ACCEPTANCE.md","# Required checks\n\nCheck a real baseline against source row identities and the declared metric. Reject a wrong-task argument, leaked input, and request after the attempt limit. Reject a nonexistent candidate identity. Demonstrate a fresh-output baseline with equal predictions. Every command result is retained by run-clean-journey-harnesses.py. Parameter validation alone is not a model-fit test.\n")
        shutil.copyfile(repo / "rsi/tools/requirements.txt",package / "requirements.txt")
        save(package / "PROVENANCE.md",f"# Generation record\n\nBuilder SHA-256: {builder_hash}. Brief SHA-256: {digest(brief_path)}. Entry SHA-256: {digest(package / 'run.py')}.\n\nThe current authoring agent read the builder skill, translated these two briefs into fixed task wrappers, and reused the learner controller. The saved driver repeats those explicit template operations. This is one author-guided generation, not an autonomous builder update or a second independent agent. Full resolved dependencies are in the journey package record.\n")
    save(out / "06-01/AMBIGUITY-REVIEW.md","# Brief review\n\nScientific choices are resolved by the task contract: prediction setting, target, input availability, MAE, time split, and two attempts. Routine choices made by the agent: Python file layout, subprocess logging, CSV evidence, and a wrapper around shared tools. Choosing the metric after running candidates is forbidden.\n")
    bike = out / "06-02/package/run.py"
    wine = out / "06-05/package/run.py"
    def call(label,script,workspace,model="constant",features="calendar",expected=0,extra=(),action="run"):
        execute(label,script,[action,"--repo",repo,"--workspace",workspace,"--model",model,"--features",features,"--hypothesis","Execute the generated brief under its fixed task and budget.",*extra],expected)
    execute("bike-inspect",repo / "rsi/tools/lab.py",["inspect","--task","bike","--workspace",out / "06-02/run"])
    call("bike-baseline",bike,out / "06-02/run")
    call("bike-leaked-feature",bike,out / "06-02/run",features="casual",expected=1)
    call("bike-exhausted",bike,out / "06-02/run",model="linear",expected=1)
    call("bike-wrong-task",bike,out / "06-02/run",expected=2,extra=["--task","wine"])
    call("bike-missing-candidate",bike,out / "06-02/run",expected=1,action="final",extra=["--candidate","trial-999"])
    save(out / "06-03/INSPECTION.md","# Generated-package inspection\n\nThe brief fixes the scientific contract; the builder fixes package structure and checks; the generated controller enforces task, attempt budget, recipe identity, and result verification at run time. Python syntax alone would not establish execution. The saved commands show both accepted and rejected paths. Shared file access remains a cooperative boundary.\n")
    save(out / "06-04/REFUSALS.md","# Actual rejection paths\n\nThe bike package admitted one baseline and one invalid leaked-feature attempt. The invalid attempt failed before fitting and consumed the second slot. The next distinct recipe was refused on budget. A wrong-task argument and nonexistent candidate identity were also rejected. No final evaluation started. See HARNESS-EXECUTION.md and the command logs.\n")
    execute("wine-inspect",repo / "rsi/tools/lab.py",["inspect","--task","wine","--workspace",out / "06-05/run"])
    call("wine-baseline",wine,out / "06-05/run",features="all")
    call("wine-logistic",wine,out / "06-05/run",model="linear",features="all")
    call("wine-compare",wine,out / "06-05/run",features="all",action="compare")
    for task,script,old in [("bike",bike,out / "06-02/run"),("wine",wine,out / "06-05/run")]:
        replay = out / "06-06" / task
        call(f"{task}-recreate",script,replay,features="calendar" if task == "bike" else "all")
        assert digest(old / "trial-001/predictions.csv") == digest(replay / "trial-001/predictions.csv")
        call(f"{task}-recreated-wrong-task",script,replay,expected=2,extra=["--task","wine" if task == "bike" else "bike"])
        save(replay / "REPEATABILITY.md",f"# Recreated baseline\n\nPrediction SHA-256: {digest(replay / 'trial-001/predictions.csv')}; identical to the original generated-package baseline. A wrong-task request still fails. This reruns saved generated code in new output state; it is not independent regeneration from prose.\n")
    save(out / "06-05/TRANSFER.md","# What changed between generated harnesses\n\nShared: data inspection, training-only transformations, attempt accounting, candidate identity, prediction checks, and recovery. Changed: target and units, time split versus duplicate-group split, regression versus classification models, MAE versus balanced accuracy, and class-recall reporting. The builder skill hash remained unchanged. An ordinal wine task would need a new target contract and metric.\n")
    for name in ["06-01","06-02","06-03","06-04","06-05","06-06"]:
        save(out / name / "PROGRESS.md","# Author progress\n\nThe recorded main harness activity completed. See HARNESS-EXECUTION.md. Five fits ran across this stage: one bike baseline, two wine fits, and two recreated baselines. Budgets are separate per declared workspace. Learner predictions, quizzes, and teach-back remain unattempted.\n")
    save(out / "PROGRESS.md","# Clean journey progress\n\nGenerated bike and wine packages executed, including actual refusals and baseline recreation. Next: inherited-improver comparison and final evaluation. No learner assessment or independent agent context was tested.\n")
    print(f"Harness stage complete: {len(calls)} child commands, five model fits, one admitted leakage failure.")


if __name__ == "__main__":
    main()

"""Historical first 02.05 driver; its launcher-PID check failed on this host.

Retained as provenance, not a validated recipe for terminating a worker. The
sealed evidence includes the failure and the stateful recovery that followed.
Do not rerun it to erase that failure or spend another experiment allocation.
"""
import csv
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path.cwd().resolve()
OUT = REPO.parent / "rsi-work-2026-09-22-interrupted-attempt"
OUT.mkdir(exist_ok=False)
WORK = OUT / "experiment"
TOOL = REPO / "rsi/tools/lab.py"
PYTHON = Path(sys.executable)
COMMANDS = []


def write(name, content):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ledger():
    with (WORK / "trials.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def command(label, args, expected):
    started = time.perf_counter()
    result = subprocess.run([str(PYTHON), "-B", *map(str,args)], capture_output=True,
                            text=True, encoding="utf-8", timeout=60)
    seconds = time.perf_counter()-started
    write(label+"-output.txt",result.stdout+result.stderr+f"\nExit: {result.returncode}\nExpected: {expected}\nSeconds: {seconds}\n")
    COMMANDS.append(f"## {label}\n\nExecutable: {PYTHON}\n\nArguments: {args!r}\n\nExit {result.returncode}; expected {expected}; process wall seconds {seconds}.\n")
    write("COMMANDS.md","# Actual commands\n\n"+"\n".join(COMMANDS))
    if result.returncode != expected:
        raise RuntimeError(f"Unexpected {label} result; inspect the retained output")
    return result


shutil.copyfile(REPO / "how-did-i-generate-it/rsi/validation/INTERRUPTED-ATTEMPT-PROTOCOL.md",OUT / "PROTOCOL.md")
shutil.copyfile(Path(__file__),OUT / "run-interrupted-attempt.py")
shutil.copyfile(TOOL,OUT / "tool-source.py")
shutil.copyfile(REPO / "rsi/tools/check_result.py",OUT / "result-checker-source.py")
write("SOURCE.md",f"# Source identities\n\nRepository: {REPO}\nTool SHA256: {digest(TOOL)}\nChecker SHA256: {digest(REPO / 'rsi/tools/check_result.py')}\nData SHA256: {digest(REPO / 'rsi/examples/bike-demand/source/hour.csv')}\nPython: {sys.version}\n\nPublic data and shared author context; no hidden evaluation boundary.\n")
write("interrupted-child.py",'''import importlib.util
from pathlib import Path
import sys
import time

source, workspace = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("course_lab", source)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

def wait_before_training(*args, **kwargs):
    (workspace / "NO-TRAINING-MARKER.txt").write_text("Admitted attempt reached a wait stub; no estimator fit called.\\n", encoding="utf-8")
    time.sleep(60)
    raise RuntimeError("Parent did not stop the fixture within its readiness budget")

lab.fit_once = wait_before_training
raise SystemExit(lab.main(["run", "--task", "bike", "--workspace", str(workspace),
    "--attempt-limit", "3", "--model", "constant", "--features", "calendar",
    "--seed", "17", "--hypothesis", "No-training interruption fixture; preserve the charged slot."]))
''')
child_args = [str(PYTHON),"-B",str(OUT / "interrupted-child.py"),str(TOOL),str(WORK)]
started = time.perf_counter()
child = subprocess.Popen(child_args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8")
try:
    deadline = time.monotonic()+20
    while not (WORK / "NO-TRAINING-MARKER.txt").exists():
        if child.poll() is not None:
            raise RuntimeError("Child exited before the intended stop point")
        if time.monotonic() >= deadline:
            raise RuntimeError("Readiness deadline expired")
        time.sleep(0.05)
    if child.poll() is not None:
        raise RuntimeError("Child not live at the stop point")
    lock = (WORK / ".running").read_text(encoding="utf-8")
    if f"pid={child.pid}\n" not in lock or ledger()[0]["status"] != "running":
        raise RuntimeError("Wrong live-process or ledger identity")
    write("LOCK-BEFORE.txt",lock)
    shutil.copyfile(WORK / "trials.csv",OUT / "LEDGER-BEFORE.csv")
    child.terminate()
    stdout,stderr = child.communicate(timeout=5)
    elapsed = time.perf_counter()-started
    if child.returncode is None or child.returncode == 0:
        raise RuntimeError("Expected terminated child")
    write("CHILD-EXIT.txt",stdout+stderr+f"\nPID: {child.pid}\nExit: {child.returncode}\nProcess wall seconds: {elapsed}\nConfirmed live before termination and terminal afterward. No estimator fit called.\n")
    COMMANDS.append(f"## interrupted-child\n\nArguments: {child_args!r}\n\nOwned PID {child.pid}; terminated after readiness marker; terminal exit {child.returncode}; wall seconds {elapsed}.\n")
finally:
    if child.poll() is None:
        child.kill()
        stdout,stderr = child.communicate(timeout=5)
        write("UNEXPECTED-CLEANUP.txt",stdout+stderr+f"\nOwned child killed during error cleanup: {child.returncode}\n")

common = [TOOL,"run","--task","bike","--workspace",WORK,"--model","linear",
          "--features","calendar","--seed","17","--hypothesis","Continue after reconciling the interrupted fixture."]
before_hash = digest(WORK / "trials.csv")
command("stale-lock-refusal",common,1)
if digest(WORK / "trials.csv") != before_hash:
    raise RuntimeError("Stale-lock refusal changed the ledger")
if child.poll() is None:
    raise RuntimeError("Never remove a live child's lock")
lock_path = (WORK / ".running").resolve()
if lock_path.parent != WORK.resolve() or lock_path.read_text(encoding="utf-8") != lock:
    raise RuntimeError("Unexpected stale lock")
lock_path.unlink()
command("running-record-refusal",common,1)
if digest(WORK / "trials.csv") != before_hash:
    raise RuntimeError("Running-record refusal changed the ledger")
records = ledger()
records[0]["status"] = "interrupted"
records[0]["note"] += " | Author confirmed owned child termination before training; elapsed process time is in CHILD-EXIT.txt."
buffer = io.StringIO(newline="")
writer = csv.DictWriter(buffer,fieldnames=list(records[0]))
writer.writeheader()
writer.writerows(records)
write("experiment/trials.csv",buffer.getvalue())
shutil.copyfile(WORK / "trials.csv",OUT / "LEDGER-RECONCILED.csv")
proposal_hash = digest(WORK / "trial-001/PROPOSAL.md")
contract_hash = digest(WORK / "CONTRACT.md")
command("real-continuation",common,0)
command("prediction-check",[REPO / "rsi/tools/check_result.py",WORK / "trial-002","--report",WORK / "trial-002/CHECK.md"],0)
records = ledger()
checks = {
    "Two charged unique attempts": [r["candidate"] for r in records] == ["trial-001","trial-002"],
    "Interrupted slot retained": records[0]["status"] == "interrupted",
    "One real continuation succeeded": records[1]["status"] == "ok",
    "First proposal preserved": digest(WORK / "trial-001/PROPOSAL.md") == proposal_hash,
    "Contract preserved": digest(WORK / "CONTRACT.md") == contract_hash,
    "Three-attempt ceiling retained": "- max_attempts: 3" in (WORK / "CONTRACT.md").read_text(encoding="utf-8").splitlines(),
    "No false first predictions": not (WORK / "trial-001/predictions.csv").exists(),
    "No final evaluation": not (WORK / "FINAL-LOCK.md").exists(),
    "No stale lock after continuation": not (WORK / ".running").exists(),
}
write("CHECKS.csv","check,passed\n"+"\n".join(f"{key},{value}" for key,value in checks.items())+"\n")
write("PROGRESS.md","# Progress\n\nThe interruption fixture and one real fit occupy two of three slots. One experiment slot remains, but this supplemental allocation is finished. No further fit is authorized by this run. No live child or stale lock remains. Learner checkpoints unattempted.\n")
if not all(checks.values()):
    raise RuntimeError("Post-run invariant failed; preserve and inspect")
print(f"PASS: terminated no-training fixture; two refusals; one checked real fit; {len(checks)} invariants.")

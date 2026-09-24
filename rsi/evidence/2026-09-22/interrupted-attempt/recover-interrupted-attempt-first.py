"""Continue the retained failed fixture. Never admit another interruption stub."""
import csv
import ctypes
from ctypes import wintypes
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path.cwd().resolve()
OUT = REPO.parent / "rsi-work-2026-09-22-interrupted-attempt"
WORK = OUT / "experiment"
TOOL = REPO / "rsi/tools/lab.py"
COMMANDS = []
if (OUT / "RECOVERY-STARTED.txt").exists():
    raise RuntimeError("Recovery already started; inspect its state instead of restarting")
(OUT / "RECOVERY-STARTED.txt").write_text("One recovery allocation started.\n",encoding="utf-8")
shutil.copyfile(Path(__file__), OUT / "recover-interrupted-attempt.py")


def write(name,text):
    (OUT / name).write_text(text,encoding="utf-8",newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ledger():
    with (WORK / "trials.csv").open(encoding="utf-8",newline="") as stream:
        return list(csv.DictReader(stream))


def require(ok,message):
    if not ok:
        raise RuntimeError(message)


def worker_is_absent(pid):
    require(sys.platform == "win32","This retained recovery uses the actual Windows host")
    kernel = ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000,False,pid)
    if not handle:
        error = ctypes.get_last_error()
        require(error == 87,f"Cannot establish process absence: Windows error {error}")
        return "OpenProcess: no such PID (error 87)"
    try:
        status = wintypes.DWORD()
        require(kernel.GetExitCodeProcess(handle,ctypes.byref(status)),"Cannot inspect worker status")
        require(status.value != 259,"Worker is live; retain lock")
        return f"Worker handle is terminal: exit {status.value}"
    finally:
        kernel.CloseHandle(handle)


def command(label,args,expected):
    started=time.perf_counter()
    result=subprocess.run([sys.executable,"-B",*map(str,args)],capture_output=True,text=True,encoding="utf-8",timeout=60)
    elapsed=time.perf_counter()-started
    write(label+"-output.txt",result.stdout+result.stderr+f"\nExit: {result.returncode}\nExpected: {expected}\nSeconds: {elapsed}\n")
    COMMANDS.append(f"## {label}\n\nExecutable: {sys.executable}\n\nArguments: {args!r}\n\nExit {result.returncode}; expected {expected}; wall seconds {elapsed}.\n")
    write("RECOVERY-COMMANDS.md","# Recovery commands\n\n"+"\n".join(COMMANDS))
    require(result.returncode == expected,f"Unexpected {label} result; inspect retained output")


lock_path=(WORK / ".running").resolve()
require(lock_path.parent == WORK.resolve(),"Unexpected lock path")
lock=lock_path.read_text(encoding="utf-8")
pid=int(dict(line.split("=",1) for line in lock.splitlines())["pid"])
write("OS-WORKER-CHECK.txt",f"PID {pid}: {worker_is_absent(pid)}\n")
records=ledger()
require(len(records)==1 and records[0]["candidate"]=="trial-001" and records[0]["status"]=="running","Unexpected existing experiment")
before_hash=digest(WORK / "trials.csv")
common=[TOOL,"run","--task","bike","--workspace",WORK,"--model","linear","--features","calendar","--seed","17","--hypothesis","Continue after reconciling the interrupted fixture."]
command("stale-lock-refusal",common,1)
require(digest(WORK / "trials.csv")==before_hash,"Refusal changed attempt count")
write("OS-WORKER-CHECK-BEFORE-REMOVAL.txt",f"PID {pid}: {worker_is_absent(pid)}\n")
require(lock_path.read_text(encoding="utf-8")==lock,"Lock changed during recovery")
lock_path.unlink()
command("running-record-refusal",common,1)
require(digest(WORK / "trials.csv")==before_hash,"Refusal changed ledger")
records[0]["status"]="interrupted"
records[0]["note"]+=" | Worker confirmed absent after failed driver cleanup; no estimator fit. Process duration unavailable; do not refund slot."
buffer=io.StringIO(newline="")
writer=csv.DictWriter(buffer,fieldnames=list(records[0]))
writer.writeheader()
writer.writerows(records)
write("experiment/trials.csv",buffer.getvalue())
shutil.copyfile(WORK / "trials.csv",OUT / "LEDGER-RECONCILED.csv")
proposal_hash=digest(WORK / "trial-001/PROPOSAL.md")
contract_hash=digest(WORK / "CONTRACT.md")
command("real-continuation",common,0)
command("prediction-check",[REPO / "rsi/tools/check_result.py",WORK / "trial-002","--report",WORK / "trial-002/CHECK.md"],0)
records=ledger()
checks={
    "Two charged unique attempts":[r["candidate"] for r in records]==["trial-001","trial-002"],
    "Interrupted slot retained":records[0]["status"]=="interrupted",
    "One real continuation succeeded":records[1]["status"]=="ok",
    "First proposal preserved":digest(WORK / "trial-001/PROPOSAL.md")==proposal_hash,
    "Contract preserved":digest(WORK / "CONTRACT.md")==contract_hash,
    "Three-attempt ceiling retained":"- max_attempts: 3" in (WORK / "CONTRACT.md").read_text(encoding="utf-8").splitlines(),
    "No false first predictions":not (WORK / "trial-001/predictions.csv").exists(),
    "No final evaluation":not (WORK / "FINAL-LOCK.md").exists(),
    "No stale lock":not (WORK / ".running").exists(),
}
write("CHECKS.csv","check,passed\n"+"\n".join(f"{key},{value}" for key,value in checks.items())+"\n")
write("PROGRESS.md","# Progress\n\nTwo of three attempt slots spent: one interrupted no-training fixture and one actual fit. Both refusal probes and the prediction check finished. One experiment slot remains, but this supplemental allocation is complete. Do not fit again. No live worker or stale lock. Learner checks unattempted.\n")
require(all(checks.values()),"Post-run invariant failed")
print(f"PASS: existing interrupted slot recovered; one checked actual fit; {len(checks)} invariants.")

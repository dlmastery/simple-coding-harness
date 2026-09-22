"""Run one frozen 24-attempt revision stage within the shared development allowance."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASKS = {3, 16, 28, 361234, 361236, 361244}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(stage):
    proposal = ROOT / f"rsi/experiments/real-tabular/revision-{stage}"
    baseline = ROOT / "rsi/evidence/2026-09-22/real-tabular-baseline"
    work = ROOT.parent / f"rsi-work-2026-09-22-real-tabular-revision-{stage}"
    if work.exists():
        raise ValueError("Fresh stage required; no retries or overwrite")
    previous = ROOT.parent / "rsi-work-2026-09-22-real-tabular-revision-1"
    if stage == 2:
        if not (previous / "COMPLETE.md").exists() or not pd.read_csv(previous / "REVISION-CHECKS.csv").passed.all():
            raise ValueError("Stage one must finish and pass independent checks first")
    planned = pd.read_csv(proposal / "PLAN.csv")
    if len(planned) != 24 or planned.attempt.tolist() != list(range(1, 25)) or set(planned.task) != TASKS or not (planned.groupby("task").size() == 4).all():
        raise ValueError("Each stage admits exactly four slots per development task")
    if stage == 2:
        previous_ledger = pd.read_csv(previous / "LEDGER.csv")
        if len(previous_ledger) != 24 or not (previous_ledger.groupby("task").size() == 4).all():
            raise ValueError("Previous charged allocation differs")
    work.mkdir()
    source = work / "source"
    source.mkdir()
    for name in ("engine.py", "PROPOSAL.md", "PLAN.csv"):
        shutil.copyfile(proposal / name, source / name)
    shutil.copyfile(baseline / "source/engine.py", source / "parent_engine.py")
    for path in (Path(__file__), Path(__file__).with_name("real_tabular_worker.py"),
                 ROOT / "how-did-i-generate-it/rsi/validation/REAL-TABULAR-DEVELOPMENT-PROTOCOL.md"):
        shutil.copyfile(path, source / path.name)
    # A stage-two module may explicitly inherit the first revision in addition
    # to the unchanged parent. Preserve that executed ancestor if requested.
    if stage == 2:
        shutil.copyfile(previous / "source/engine.py", source / "revision_one_engine.py")
    shutil.copytree(baseline / "public", work / "public")
    for name in ("PANEL.csv", "ENVIRONMENT.md"):
        shutil.copyfile(baseline / name, work / name)
    shutil.copyfile(baseline / "LEDGER.csv", work / "PARENT-LEDGER.csv")
    planned.to_csv(work / "PLANNED.csv", index=False)
    (work / "ANCESTRY.md").write_text(f"# Source inheritance\n\nStage: {stage}\nParent engine SHA256: {sha(source / 'parent_engine.py')}\n"
        f"Parent archive: {baseline}\nDevelopment allocation: {stage * 24} of 48 admitted revision slots through this stage.\n")
    frozen = [dict(path=p.relative_to(work).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
              for p in sorted(work.rglob("*")) if p.is_file()]
    pd.DataFrame(frozen).to_csv(work / "SOURCE-AND-INPUT-FREEZE.csv", index=False)
    power = work / "POWER.md"
    if os.name == "nt":
        if ctypes.windll.kernel32.SetThreadExecutionState(0x80000001) == 0:
            raise OSError("Idle-sleep prevention refused before fits")
        power.write_text(f"# Temporary idle-sleep prevention\n\nStarted UTC: {datetime.now(timezone.utc).isoformat()}\nPID: {os.getpid()}\nNo persistent setting changed.\n")
    env = os.environ.copy()
    env.update({name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    env["PYTHONHASHSEED"] = "41"
    ledger = []
    try:
        for row in planned.to_dict("records"):
            output = work / "attempts" / f"{row['attempt']:03d}"
            output.mkdir(parents=True)
            command = [sys.executable, str(source / "real_tabular_worker.py"), "--task", str(work / "public" / str(row["task"])),
                       "--engine", str(source / "engine.py"), "--candidate", row["candidate"], "--kind", row["kind"], "--output", str(output)]
            (output / "ADMITTED.md").write_text(f"# Admitted revision attempt\n\nStage {stage}: {row}\nUTC: {datetime.now(timezone.utc).isoformat()}\nLimit: 30 worker-process seconds\n")
            start = time.perf_counter()
            with (output / "stdout.txt").open("w") as stdout, (output / "stderr.txt").open("w") as stderr:
                process = subprocess.Popen(command, cwd=output, env=env, stdout=stdout, stderr=stderr)
                (output / ".running").write_text(str(process.pid))
                try:
                    process.wait(timeout=30)
                    status = "success" if process.returncode == 0 else "failed"
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    status = "timeout"
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    (output / ".running").unlink()
            record = dict(**row, status=status, exit_code=process.returncode, worker_seconds=time.perf_counter() - start)
            if status == "success":
                metrics = pd.read_csv(output / "METRICS.csv").set_index("split")
                record.update(selection_score=metrics.loc["selection", "score"], selection_loss=metrics.loc["selection", "loss"])
            ledger.append(record)
            pd.DataFrame(ledger).to_csv(work / "LEDGER.csv", index=False)
            print(f"Stage {stage} {row['attempt']:02d}/24 task {row['task']} {row['candidate']}: {status}; loss {record.get('selection_loss', 'NA')}; {record['worker_seconds']:.2f}s", flush=True)
    finally:
        if os.name == "nt":
            result = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            with power.open("a") as file:
                file.write(f"Released UTC: {datetime.now(timezone.utc).isoformat()}; return {result}\n")
    (work / "COMPLETE.md").write_text(f"# Revision stage {stage} completed\n\n24 attempts admitted. Independent prediction checks required. No final scoring.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=int, choices=[1, 2])
    run(parser.parse_args().stage)

"""Freeze and run the declared 48-attempt development portfolio; no final access."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CANDIDATES = ["linear", "extra-trees", "hist-boost", "random-forest", "rbf-1", "rbf-10", "neighbors-5", "neighbors-25"]
TASKS = {3, 16, 28, 361234, 361236, 361244}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(work):
    if work.exists():
        raise ValueError("Fresh workspace required; no automatic retries")
    work.mkdir(parents=True)
    source = work / "source"
    source.mkdir()
    for path in (Path(__file__), ROOT / "how-did-i-generate-it/rsi/scripts/real_tabular_worker.py",
                 ROOT / "rsi/experiments/real-tabular/engine.py",
                 ROOT / "how-did-i-generate-it/rsi/validation/REAL-TABULAR-DEVELOPMENT-PROTOCOL.md"):
        shutil.copyfile(path, source / path.name)
    data = ROOT / "rsi/evidence/2026-09-22/real-tabular-data-v2"
    panel = pd.read_csv(data / "DATASET-PANEL.csv")
    panel = panel[panel.task.isin(TASKS)]
    assert set(panel.task) == TASKS and (panel.role == "development").all()
    panel.to_csv(work / "PANEL.csv", index=False)
    for task in sorted(TASKS):
        destination = work / "public" / str(task)
        destination.mkdir(parents=True)
        for filename in ("train.csv", "selection.csv", "SCHEMA.csv"):
            original = data / "tasks" / str(task) / ("" if filename == "SCHEMA.csv" else "public") / filename
            shutil.copyfile(original, destination / filename)
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl")}
    (work / "ENVIRONMENT.md").write_text(f"# Execution environment\n\nPython: {sys.version}\nPlatform: {platform.platform()}\n\n" +
        "\n".join(f"{name}: {value}" for name, value in versions.items()) + "\n", encoding="utf-8")
    planned = [dict(attempt=i * 8 + j + 1, task=int(row.task), kind=row.kind, candidate=candidate)
               for i, row in enumerate(panel.itertuples()) for j, candidate in enumerate(CANDIDATES)]
    pd.DataFrame(planned).to_csv(work / "PLANNED.csv", index=False)
    frozen = [dict(path=p.relative_to(work).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
              for p in sorted(work.rglob("*")) if p.is_file()]
    pd.DataFrame(frozen).to_csv(work / "SOURCE-AND-INPUT-FREEZE.csv", index=False)
    ledger = []
    power = work / "POWER.md"
    if os.name == "nt":
        result = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        if result == 0:
            raise OSError("Temporary idle-sleep prevention failed before fitting")
        power.write_text(f"# Temporary idle-sleep prevention\n\nStarted UTC: {datetime.now(timezone.utc).isoformat()}\nPID: {os.getpid()}\nNo persistent setting changed.\n")
    env = os.environ.copy()
    env.update({name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    env["PYTHONHASHSEED"] = "41"
    try:
        for plan in planned:
            output = work / "attempts" / f"{plan['attempt']:03d}"
            output.mkdir(parents=True)
            command = [sys.executable, str(source / "real_tabular_worker.py"), "--task", str(work / "public" / str(plan["task"])),
                       "--engine", str(source / "engine.py"), "--candidate", plan["candidate"], "--kind", plan["kind"], "--output", str(output)]
            (output / "ADMITTED.md").write_text(f"# Admitted attempt\n\n{plan}\nUTC: {datetime.now(timezone.utc).isoformat()}\nLimit: 30 worker-process seconds\n")
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
            elapsed = time.perf_counter() - start
            record = dict(**plan, status=status, exit_code=process.returncode, worker_seconds=elapsed)
            if status == "success":
                metrics = pd.read_csv(output / "METRICS.csv").set_index("split")
                record.update(selection_loss=metrics.loc["selection", "loss"], selection_score=metrics.loc["selection", "score"])
            ledger.append(record)
            pd.DataFrame(ledger).to_csv(work / "LEDGER.csv", index=False)
            print(f"{plan['attempt']:02d}/48 task {plan['task']} {plan['candidate']}: {status}; loss {record.get('selection_loss', 'NA')}; {elapsed:.2f}s", flush=True)
    finally:
        if os.name == "nt":
            result = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            with power.open("a") as file:
                file.write(f"Released UTC: {datetime.now(timezone.utc).isoformat()}; return {result}\n")
    (work / "COMPLETE.md").write_text("# Development portfolio completed\n\n48 attempts admitted. Check all predictions independently before interpreting scores. No final scoring.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    run(parser.parse_args().workspace.resolve())

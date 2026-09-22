"""Two-stage author exploration: stop for a recorded decision before fit three."""
import argparse
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time
import pandas as pd

repo=Path(__file__).resolve().parents[3]
out=repo.parent / "rsi-work-2026-09-21-exploration"
experiment=out / "experiment"
phase=argparse.ArgumentParser()
phase.add_argument("phase", choices=["probes","finish"])
args=phase.parse_args()
def save(name,text):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def commands(label,parts):
    start=time.perf_counter()
    result=subprocess.run([sys.executable,*map(str,parts)],cwd=repo,capture_output=True,text=True,timeout=60)
    seconds=time.perf_counter()-start
    save("commands/"+label+".md",f"# {label}\n\nExit: {result.returncode}\nWall seconds: {seconds:.6f}\n\nStdout:\n{result.stdout}\nStderr:\n{result.stderr or '(empty)'}")
    with (out/"COMMANDS.csv").open("a",encoding="utf-8",newline="") as stream:
        csv.writer(stream).writerow([label,result.returncode,f"{seconds:.6f}"])
    if result.returncode:raise SystemExit("Command failed; preserve attempt: "+label)
def fit(model,features,hypothesis,index):
    commands(f"fit-{index}",[repo/"rsi/tools/lab.py","run","--task","bike","--workspace",experiment,"--model",model,"--features",features,"--seed","17","--attempt-limit","3","--hypothesis",hypothesis])
    candidate=experiment/f"trial-{index:03d}"
    commands(f"check-{index}",[repo/"rsi/tools/check_result.py",candidate,"--report",candidate/"CHECK.md"])
if args.phase=="probes":
    if out.exists():raise SystemExit("Preserve existing workspace")
    out.mkdir()
    shutil.copyfile(__file__,out/"run-exploration.py")
    shutil.copyfile(repo/"how-did-i-generate-it/rsi/validation/EXPLORATION-PROTOCOL.md",out/"PROTOCOL.md")
    save("COMMANDS.csv","action,exit,wall_seconds")
    save("ALLOCATION.md","# Frozen allowance\n\nOne experiment: three fits total, seed 17, selection only. Initial probes are constant/calendar then linear/calendar. Read the saved protocol for the declared third-choice rule. No final evaluation or memory-file load. Existing duplicate evidence is inspected separately without a fourth fit.")
    save("TOOL-HASHES.csv","path,sha256\n"+"\n".join(p+","+sha(repo/p) for p in ["rsi/tools/lab.py","rsi/tools/check_result.py","rsi/examples/bike-demand/source/hour.csv"]))
    fit("constant","calendar","Measure what a training-median predictor misses without input variation.",1)
    fit("linear","calendar","Test whether calendar structure reduces the baseline selection error.",2)
    predictions=pd.read_csv(experiment/"trial-002/predictions.csv")
    data=pd.read_csv(repo/"rsi/examples/bike-demand/source/hour.csv")
    selected=data.iloc[predictions.source_row.to_numpy()].copy()
    if not selected.dteday.str.startswith("2012-").all() or not (selected.dteday<"2012-07-01").all():
        raise SystemExit("Unexpected selection rows")
    selected["residual"]=predictions.actual.to_numpy()-predictions.predicted.to_numpy()
    selected["absolute_error"]=selected.residual.abs()
    for name,column in [("weather","weathersit"),("hour","hr")]:
        grouped=selected.groupby(column).agg(n=("residual","size"),mean_residual=("residual","mean"),mae=("absolute_error","mean"))
        grouped.to_csv(out/(name+"-errors.csv"))
    weather=pd.read_csv(out/"weather-errors.csv")
    supported=weather[weather.n>=50]
    gap=float(supported.mean_residual.max()-supported.mean_residual.min()) if len(supported)>=2 else 0.0
    expected="linear/all" if gap>10 else "tree/calendar"
    save("OBSERVATIONS.md",f"# Before the third fit\n\nWeather-category residual range among groups with at least 50 selection rows: {gap:.6f} rentals per hour. Declared rule suggests {expected}. Group differences can reflect calendar mix or other confounding; they motivate a controlled feature probe, not a causal claim. Read hourly and weather error CSVs and both candidate results before writing DECISION.md.\n\nNo third fit has run. One fit remains. The author has prior exposure to this dataset.")
    save("SUGGESTED-RECIPE.txt",expected)
    save("PROGRESS.md","# Paused at author decision\n\nTwo fits and two checks complete. One fit and one check remain. Read OBSERVATIONS.md; write DECISION.md naming Model and Features on separate lines before resuming. No learner checkpoints attempted.")
    print((out/"OBSERVATIONS.md").read_text(encoding="utf-8"))
else:
    if not (out/"DECISION.md").exists():raise SystemExit("A recorded decision is required")
    rows=pd.read_csv(experiment/"trials.csv")
    if len(rows)!=2 or not (rows.status=="ok").all():raise SystemExit("Expected exactly two successful probes")
    for record in csv.DictReader((out/"TOOL-HASHES.csv").open(encoding="utf-8")):
        if sha(repo/record["path"])!=record["sha256"]:raise SystemExit("Frozen source changed")
    decision=(out/"DECISION.md").read_text(encoding="utf-8")
    fields=dict(line.split(": ",1) for line in decision.splitlines() if ": " in line)
    model,features=fields["Model"],fields["Features"]
    if model+"/"+features != (out/"SUGGESTED-RECIPE.txt").read_text(encoding="utf-8").strip():raise SystemExit("Decision differs from declared rule; revise protocol, not silently continue")
    decision_hash=sha(out/"DECISION.md")
    save("DECISION-FREEZE.md","# Before fit three\n\nDECISION.md SHA-256: "+decision_hash+"\nTwo completed fits; one remaining slot. No final evaluation.")
    fit(model,features,fields["Hypothesis"],3)
    if sha(out/"DECISION.md")!=decision_hash:raise SystemExit("Decision changed after fitting")
    rows=pd.read_csv(experiment/"trials.csv")
    if len(rows)!=3:raise SystemExit("Fit count differs from allowance")
    old=repo/"rsi/evidence/2026-09-20/loops-and-systems/02-06/arm-a"
    first_hash=sha(old/"trial-001/predictions.csv");second_hash=sha(old/"trial-002/predictions.csv")
    if first_hash!=second_hash:raise SystemExit("Earlier repeat evidence differs from its description")
    save("DUPLICATE-COMPARISON.md",f"# Existing duplicate evidence\n\nThe 02.06 arm-A baseline repeat has identical prediction hashes: {first_hash}. Its two recorded fits are historical evidence. No duplicate was fitted in this three-attempt run. A deterministic repeat can check reproducibility; it does not test weather or another new mechanism. Comparing this history with the current focused probe is illustrative, not a newly randomized three-attempt comparison.\n\nSource: rsi/evidence/2026-09-20/loops-and-systems/02-06/arm-a/")
    table="| Candidate | Model | Features | Selection MAE | Fit seconds |\n|---|---|---|---:|---:|\n"+"\n".join(f"| {r.candidate} | {r.model} | {r.features} | {r.score:.6f} | {r.seconds:.6f} |" for r in rows.itertuples())
    save("EXPLORATION-REPORT.md","# Three measured fits\n\n"+table+f"\n\nThird minus calendar-only MAE: {rows.iloc[2].score-rows.iloc[1].score:.6f}; negative means lower error. The decision preceded fit three and its hash remained fixed. All three result checks exited 0. No final evaluation. Measured fit time totals {rows.seconds.sum():.6f} seconds; subprocess wall times are separate. Agent inference, proposal, and review cost are unknown. This is a fixed exploration heuristic on an author-known task, not an independently discovered or improved improver.\n")
    save("PROGRESS.md","# Author progress\n\nThree fits and three result checks complete. No fit allowance remains. Existing duplicate evidence inspected without another fit. Decision hash unchanged. No task-memory file loaded, but author context had prior dataset exposure. Learner predictions, teach-back, and quiz untested.")
    files=sorted(p for p in out.rglob("*") if p.is_file())
    save("MANIFEST.csv","file,sha256\n"+"\n".join(p.relative_to(out).as_posix()+","+sha(p) for p in files))
    print((out/"EXPLORATION-REPORT.md").read_text(encoding="utf-8"))

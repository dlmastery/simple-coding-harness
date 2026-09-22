"""Bounded author memory activities with explicit pauses before actor decisions."""
import argparse
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

repo=Path(__file__).resolve().parents[3]
out=repo.parent/"rsi-work-2026-09-21-memory-labs"
parser=argparse.ArgumentParser()
parser.add_argument("phase",choices=["outcome","probes","finish","retrieval"])
args=parser.parse_args()
def save(name,body):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(body.rstrip()+"\n",encoding="utf-8",newline="\n")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fields(path):return dict(line.split(": ",1) for line in path.read_text(encoding="utf-8").splitlines() if ": " in line)
def guard_absent(name):
    if (out/name).exists():raise SystemExit("Preserve completed phase: "+name)
def mark(name):save(name,"Completed "+args.phase+" phase. Do not rerun.")
def manifest():
    files=sorted(p for p in out.rglob("*") if p.is_file() and p.name!="MANIFEST.csv")
    save("MANIFEST.csv","file,sha256\n"+"\n".join(p.relative_to(out).as_posix()+","+sha(p) for p in files))
def append_csv(name,header,row):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    exists=path.exists()
    with path.open("a",encoding="utf-8",newline="") as stream:
        writer=csv.writer(stream,lineterminator="\n")
        if not exists:writer.writerow(header)
        writer.writerow(row)
def memory_check():
    frozen=fields(out/"10-05/FREEZE.md")
    if sha(out/"10-04/MEMORY.md")!=frozen["Memory SHA-256"]:raise SystemExit("Frozen memory changed")
    if sha(out/"10-05/data.csv")!=frozen["Data SHA-256"]:raise SystemExit("Frozen data changed")
    return frozen
calendar=["sin_hour","cos_hour","weekend"]
weather=["temperature","humidity"]
def fit(arm,number,group,data):
    folder=f"10-05/{arm}/trial-{number:03d}"
    guard_absent(folder)
    ledger=out/f"10-05/{arm}/FITS.csv"
    used=len(pd.read_csv(ledger)) if ledger.exists() else 0
    if used!=number-1 or number>2:raise SystemExit("Fit allowance/state mismatch")
    columns=calendar+(weather if group=="all" else [])
    save(folder+"/BEFORE.md",f"# Before fitting\n\nArm: {arm}\nCandidate: trial-{number:03d}\nFeatures: {group}\nEstimator: StandardScaler then Ridge alpha 10\nAllocated fits: 2\nPreviously used: {used}\nData SHA-256: {sha(out/'10-05/data.csv')}\nNo evaluation-row access for selection.")
    append_csv(f"10-05/{arm}/FITS.csv",["candidate","status","features","selection_mae","fit_seconds"],[f"trial-{number:03d}","started",group,"",""])
    train=data[data.role=="train"];selection=data[data.role=="selection"]
    model=make_pipeline(StandardScaler(),Ridge(alpha=10))
    start=time.perf_counter();model.fit(train[columns],train.target);elapsed=time.perf_counter()-start
    predicted=model.predict(selection[columns]);score=mean_absolute_error(selection.target,predicted)
    pd.DataFrame({"row_id":selection.row_id,"actual":selection.target,"predicted":predicted}).to_csv(out/folder/"selection-predictions.csv",index=False,lineterminator="\n")
    model_path=out/folder/"model.joblib";joblib.dump(model,model_path)
    save(folder+"/MODEL.sha256",sha(model_path))
    records=pd.read_csv(ledger);records.loc[len(records)-1,["status","selection_mae","fit_seconds"]]=["ok",score,elapsed]
    records.to_csv(ledger,index=False,lineterminator="\n")
    save(folder+"/RESULT.md",f"# Selection result\n\nMAE: {score:.9f}\nFit seconds: {elapsed:.6f}\nFeatures: {', '.join(columns)}\nSynthetic regression, same fixed split. No claim of agent-context isolation.")
    return predicted,score

if args.phase=="outcome":
    if out.exists():raise SystemExit("Preserve existing workspace")
    out.mkdir()
    shutil.copyfile(__file__,out/"run-memory-labs.py")
    shutil.copyfile(repo/"how-did-i-generate-it/rsi/validation/MEMORY-LABS-PROTOCOL.md",out/"PROTOCOL.md")
    original=repo.parent/"rsi-work-2026-09-21-exploration/experiment/trial-003"
    if not original.exists():raise SystemExit("Original exploration workspace missing")
    save("ENVIRONMENT.md",f"# Environment\n\nPython {sys.version.split()[0]}; scikit-learn {sklearn.__version__}; NumPy {np.__version__}; pandas {pd.__version__}.\nDriver SHA-256: {sha(Path(__file__))}")
    save("10-04/BEFORE.md","# Outcome-only check\n\nSource: rsi-work-2026-09-21-exploration/experiment/trial-003. One checker call, zero fits. The result does not authorize or approve a memory lesson.\nPrediction SHA-256: "+sha(original/"predictions.csv"))
    start=time.perf_counter()
    result=subprocess.run([sys.executable,str(repo/"rsi/tools/check_result.py"),str(original),"--report",str(out/"10-04/OUTCOME.md")],cwd=repo,capture_output=True,text=True,timeout=60)
    save("10-04/EXECUTION.md",f"# Outcome check execution\n\nExit: {result.returncode}\nWall seconds: {time.perf_counter()-start:.6f}\n\n{result.stdout}\n{result.stderr}")
    if result.returncode:raise SystemExit("Outcome check failed; do not write a success lesson")
    mark("10-04/OUTCOME-DONE.md")
    print(result.stdout)
elif args.phase=="probes":
    guard_absent("10-05")
    if not (out/"10-04/MEMORY.md").exists():raise SystemExit("Actor memory is required")
    save("10-05/EXPOSURE.md","# Actual exposure\n\nBoth arms are designed by the same author in one context. That author has read MEMORY.md. The no-memory execution path does not open that file, but this is not a clean no-memory agent context. Separate model fits do not erase author knowledge. The common strategy lets both arms inspect residuals against unused permitted inputs. Memory is not the sole source of that strategy.")
    save("10-05/ALLOCATION.md","# Matched budget\n\nTwo fits per arm; four total. One initial calendar fit, one recorded follow-up per arm. Both use the same generated rows, scaler, Ridge alpha 10, selection metric, and tie rule. Evaluation uses already fitted models. No memory updates during either arm.")
    rng=np.random.default_rng(61005);n=480
    hour=rng.integers(0,24,n);weekend=rng.integers(0,7,n)>=5
    temp=rng.uniform(5,30,n);humidity=rng.uniform(.2,.95,n)
    sin=np.sin(2*np.pi*hour/24);cos=np.cos(2*np.pi*hour/24)
    target=120+30*sin+12*cos+8*weekend+4*temp-18*humidity+rng.normal(0,8,n)
    data=pd.DataFrame({"row_id":np.arange(n),"role":["train"]*280+["selection"]*100+["evaluation"]*100,"sin_hour":sin,"cos_hour":cos,"weekend":weekend.astype(int),"temperature":temp,"humidity":humidity,"target":target})
    data.to_csv(out/"10-05/data.csv",index=False,lineterminator="\n")
    save("10-05/TASK.md","# Synthetic demand fixture\n\nPredict a synthetic continuous demand value from generated calendar and weather measurements. Units are constructed demand units per observation. This is not a real rental dataset or a future-weather forecast. Seed 61005; 480 IID generated rows; fixed split 280/100/100. Training rows alone fit preprocessing. Calendar features: sin_hour, cos_hour, weekend. Weather group: temperature, humidity. Source generator is in the retained driver. The host can inspect all labels and the generating formula; evaluation is a cooperative boundary, not secrecy.")
    save("10-05/FREEZE.md",f"# Before either fit\n\nMemory SHA-256: {sha(out/'10-04/MEMORY.md')}\nData SHA-256: {sha(out/'10-05/data.csv')}\nPolicy: add weather when absolute selection residual correlation with temperature exceeds 0.2; otherwise deliberately repeat calendar within the second slot.\nSelection: lower MAE; ties retain trial-001.\nNo memory writes until the separate adaptation-copy activity.")
    for arm in ["no-memory","memory"]:
        if arm=="memory":
            content=(out/"10-04/MEMORY.md").read_text(encoding="utf-8")
            save(f"10-05/{arm}/MEMORY-READ.md","# Frozen memory read\n\nSHA-256: "+sha(out/"10-04/MEMORY.md")+"\n\n"+content)
        else:save(f"10-05/{arm}/MEMORY-READ.md","# No memory-file read in this path\n\nThe author context has already seen the note. This is a shared-context demonstration, not controlled erasure.")
        predicted,score=fit(arm,1,"calendar",data)
        selection=data[data.role=="selection"]
        residual=selection.target.to_numpy()-predicted
        correlation=float(np.corrcoef(residual,selection.temperature)[0,1])
        save(f"10-05/{arm}/OBSERVATIONS.md",f"# Before follow-up\n\nCalendar selection MAE: {score:.9f}\nResidual/temperature correlation: {correlation:.9f}\nSuggested features: {'all' if abs(correlation)>.2 else 'calendar'}\nOne fit remains. This correlation motivates a controlled feature probe; it is not causal evidence.")
    memory_check();mark("10-05/PROBES-DONE.md")
    print("Two baseline fits completed. Read both observations and write separate DECISION.md files before finish.")
elif args.phase=="finish":
    guard_absent("10-05/FINISH-DONE.md")
    memory_check();data=pd.read_csv(out/"10-05/data.csv")
    for arm in ["no-memory","memory"]:
        decision=out/f"10-05/{arm}/DECISION.md"
        if not decision.exists():raise SystemExit("Recorded actor decision missing")
        group=fields(decision)["Features"]
        if group!=fields(out/f"10-05/{arm}/OBSERVATIONS.md")["Suggested features"]:raise SystemExit("Decision differs from declared rule")
        save(f"10-05/{arm}/DECISION-FREEZE.md","# Before follow-up fit\n\nSHA-256: "+sha(decision))
        fit(arm,2,group,data)
        if sha(decision)!=fields(out/f"10-05/{arm}/DECISION-FREEZE.md")["SHA-256"]:
            raise SystemExit("Actor decision changed during follow-up")
    chosen=[]
    for arm in ["no-memory","memory"]:
        records=pd.read_csv(out/f"10-05/{arm}/FITS.csv")
        best=records.sort_values(["selection_mae","candidate"]).iloc[0]
        chosen.append((arm,best.candidate,best.features,float(best.selection_mae)))
    save("10-05/CHOICES.csv","arm,candidate,features,selection_mae\n"+"\n".join(",".join(map(str,row)) for row in chosen))
    choice_hash=sha(out/"10-05/CHOICES.csv")
    save("10-05/CHOICES-FREEZE.md","# Before evaluation predictions\n\nSHA-256: "+choice_hash+"\nBoth choices fixed. No further fits or selection edits.")
    results=[];evaluation=data[data.role=="evaluation"]
    for arm,candidate,group,selection_score in chosen:
        folder=out/f"10-05/{arm}/{candidate}";model_path=folder/"model.joblib"
        if sha(model_path)!=(folder/"MODEL.sha256").read_text().strip():raise SystemExit("Local model identity changed")
        model=joblib.load(model_path)  # Trusted model generated locally in this run, hash checked above.
        predicted=model.predict(evaluation[calendar+(weather if group=="all" else [])])
        report=pd.DataFrame({"row_id":evaluation.row_id,"actual":evaluation.target,"predicted":predicted})
        report.to_csv(out/f"10-05/{arm}/evaluation-predictions.csv",index=False,lineterminator="\n")
        score=float(mean_absolute_error(evaluation.target,predicted))
        reread=pd.read_csv(out/f"10-05/{arm}/evaluation-predictions.csv")
        checked=float(np.mean(np.abs(reread.actual-reread.predicted)))
        if list(reread.row_id)!=list(evaluation.row_id) or not np.allclose(reread.actual,evaluation.target,rtol=0,atol=1e-12) or abs(score-checked)>1e-9:raise SystemExit("Evaluation record failed recomputation")
        results.append((arm,candidate,score))
    if sha(out/"10-05/CHOICES.csv")!=choice_hash:raise SystemExit("Choices changed")
    memory_check()
    save("10-05/EVALUATION.csv","arm,candidate,mae\n"+"\n".join(",".join(map(str,row)) for row in results))
    save("10-05/RESULTS.md","# Frozen-memory demonstration\n\n"+"\n".join(f"{arm}: {candidate}, evaluation MAE {score:.9f}." for arm,candidate,score in results)+f"\n\nMemory minus no-memory MAE: {results[1][2]-results[0][2]:.9f}. Both actors used the same declared residual rule. The shared author context prevents a clean memory-effect attribution. Memory and input hashes stayed fixed. Four fits total; no evaluation refits. File stability is not context isolation. Agent costs are unknown.")
    mark("10-05/FINISH-DONE.md")
    print((out/"10-05/RESULTS.md").read_text())
elif args.phase=="retrieval":
    guard_absent("10-06")
    if not (out/"10-05/FINISH-DONE.md").exists():raise SystemExit("Complete the evaluation first")
    save("10-06/CONTRACT.md","# New working-state fixture\n\nRun: new-fixture\nCandidate: trial-001\nPending: inspect selection residuals\nSimulated limit: 2\nSimulated used: 1\n\nThis is a constructed partially completed state, not an actual fit or authorization to train. This lab permits zero fits.")
    contract=fields(out/"10-06/CONTRACT.md")
    save("10-06/WORKING.md","# Current working state\n\nRun: "+contract["Run"]+"\nCandidate: "+contract["Candidate"]+"\nPending: "+contract["Pending"]+"\nSimulated remaining: 1\nUpdate rule: only this run's own ledger changes its state.\nNo fits are authorized in this retrieval exercise.")
    save("10-06/EXPERIENCE.md","# Reusable experience\n\nKind: experience\nScope: tabular prediction audits with retained row IDs and pinned targets\nSource: exploration/trial-003 and the 10-04 outcome check\nInstruction: compare prediction row identities and source targets before accepting a reported score.\nUpdate rule: revise this scoped lesson only in a separately declared learning phase. Do not import historical candidate IDs or attempt counts.")
    save("10-06/STALE-WORKING.md","# Historical state fixture\n\nRun: exploration\nCandidate: trial-001\nPending: fit the next recipe\nSimulated remaining: 2\n\nThe candidate string collides with the new run's candidate. Its run identity and budget do not transfer.")
    original=sha(out/"10-06/WORKING.md")
    experience=fields(out/"10-06/EXPERIENCE.md")
    ok=experience["Kind"]=="experience" and "row IDs" in experience["Scope"]
    save("10-06/RETRIEVAL-1.md","# Scoped retrieval\n\n"+("PASS" if ok else "REJECT")+"\nRetrieved the reusable row-identity principle. The current run, candidate, pending action, and simulated remaining value stay in WORKING.md. This gate recognizes the declared record type and scope, not arbitrary semantic relevance.")
    stale=fields(out/"10-06/STALE-WORKING.md")
    accepted=stale["Run"]==contract["Run"] and stale["Candidate"]==contract["Candidate"]
    save("10-06/RETRIEVAL-2.md","# Stale-state fixture\n\n"+("ACCEPT" if accepted else "REJECT")+"\nCandidate labels match, but run identities differ: exploration versus new-fixture. Do not import the historical pending action or remaining budget.")
    if not ok or accepted or sha(out/"10-06/WORKING.md")!=original:raise SystemExit("Retrieval boundary failed")
    save("10-06/MERGED-COPY.md",(out/"10-06/WORKING.md").read_text()+"\n"+(out/"10-06/EXPERIENCE.md").read_text()+"\n"+(out/"10-06/STALE-WORKING.md").read_text())
    save("10-06/AMBIGUITY.md","# Ambiguous merged instruction\n\nThe copy names two runs and two remaining-budget values under the same candidate string. An instruction to fit the next recipe now conflicts with the new run's pending residual inspection. Record boundaries resolve the ambiguity; do not execute the concatenated note as a current plan. No additional retrieval check or fit was run.")
    mark("10-06/RETRIEVAL-DONE.md")
    manifest();print("Two retrieval checks completed; current state unchanged; zero fits.")

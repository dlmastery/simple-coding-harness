"""Read archived run evidence and render distinct explanatory views; no ML execution."""
import csv
import hashlib
import re
import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

repo = Path(__file__).resolve().parents[3]
out = repo.parent / "rsi-work-2026-09-21-three-views"
if out.exists():
    raise SystemExit("Preserve existing workspace.")
out.mkdir()
def save(name, body):
    (out / name).write_text(body.rstrip() + "\n", encoding="utf-8", newline="\n")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
root = repo / "rsi/evidence/2026-09-20/clean-journey"
sources = [root / p for p in [
    "COMMANDS.md", "00-03/CONTRACT.md", "00-03/trials.csv", "00-03/trial-001/predictions.csv",
    "00-03/trial-001/RESULT.md", "00-03/trial-001/CHECK.md", "STRUCTURE-CHECKS.md",
    "03-05/diagnostic/REPORT-FAILURE.md", "03-05/diagnostic/RECOVERED-REPORT.md",
    "03-05/diagnostic/trial-001/predictions.csv", "03-05/diagnostic/trial-001/CHECK.md",
    "03-05/diagnostic/trials.csv"
]] + [repo / "how-did-i-generate-it/rsi/scripts/run-clean-journey-structure.py", repo / "rsi/tools/check_result.py"]
identities = [(p.relative_to(repo).as_posix(), sha(p)) for p in sources]
save("SOURCES.csv", "repository_path,sha256\n" + "\n".join(",".join(row) for row in identities))
shutil.copyfile(__file__, out / "build-three-views.py")
shutil.copyfile(repo / "how-did-i-generate-it/rsi/validation/THREE-VIEWS-PROTOCOL.md", out / "PROTOCOL.md")
commands = (root / "COMMANDS.md").read_text(encoding="utf-8")
events = [line for line in commands.splitlines() if "00-03-constant-calendar" in line or "00-03-check-trial-001" in line]
if len(events) != 2 or any("| 0 | 0 |" not in line for line in events):
    raise SystemExit("Expected successful archived command pair not found.")
with (root / "00-03/trials.csv").open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
if len(rows) != 1 or rows[0]["candidate"] != "trial-001" or rows[0]["status"] != "ok":
    raise SystemExit("Unexpected candidate ledger.")
pred_hash = sha(root / "00-03/trial-001/predictions.csv")
recovered = (root / "03-05/diagnostic/RECOVERED-REPORT.md").read_text(encoding="utf-8")
if pred_hash != sha(root / "03-05/diagnostic/trial-001/predictions.csv") or pred_hash not in recovered:
    raise SystemExit("Recovery prediction identity does not agree.")
score = float(rows[0]["score"])
if f"{score:.6f}" not in recovered:
    raise SystemExit("Archived score does not agree.")
save("RECORD-CHECK.md", f"# Current archive inspection\n\nTwo recorded subprocesses exited 0. Candidate trial-001 is a successful bike/constant/calendar recipe with seed {rows[0]['seed']}. Its archived score is {score:.6f}. Prediction SHA-256 agrees across original and recovery copy and the recovered report. No model or checker reran in this audit.\n\n" + "\n".join(events))
save("control-plan.mmd", '''flowchart LR
  fit["Fit and predict: trial-001"] --> check["Check saved result"]
  check -->|passes| accept["Use checked score"]
  check -->|fails| stop["Stop; preserve failure"]
  accept --> report["Write presentation report"]
  report -->|fails| error["Retain exception"]
  error --> recheck["Recheck unchanged predictions"]
  recheck --> recovered["Write recovered report"]''')
save("revised-plan.mmd", '''flowchart LR
  fit["Fit and predict"] --> check["Check result"]
  check --> units["NEW: validate MAE unit label"]
  units --> report["Use checked score and write report"]
  note["Plan edit only: units check did not run"]''')

plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":12, "svg.fonttype":"none"})
colors = {"blue":"#eaf2fb", "green":"#e8f4ee", "red":"#fbe9e7", "amber":"#fff3d9", "gray":"#f1f3f5"}
def canvas(title, subtitle):
    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set(xlim=(0,14), ylim=(0,7)); ax.axis("off")
    ax.text(.35,6.6,title,fontsize=22,weight="bold",color="#183249")
    ax.text(.35,6.15,subtitle,fontsize=11,color="#415568")
    return fig,ax
def box(ax,x,y,w,h,title,body,color="blue"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.08,rounding_size=0.10",linewidth=1.2,edgecolor="#6c8598",facecolor=colors[color]))
    ax.text(x+.17,y+h-.30,title,fontsize=12,weight="bold",va="top",color="#183249")
    ax.text(x+.17,y+h-.78,body,fontsize=10.5,va="top",linespacing=1.5,color="#243d50")
def arrow(ax,a,b,label=None):
    ax.annotate("",xy=b,xytext=a,arrowprops={"arrowstyle":"->","color":"#47687f","lw":1.5})
    if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.15,label,fontsize=9,ha="center",color="#47687f")
def finish(fig,ax,name,footer):
    ax.text(.35,.22,footer,fontsize=10,color="#415568")
    fig.savefig(out / (name+".png"),facecolor="white",bbox_inches="tight")
    fig.savefig(out / (name+".svg"),facecolor="white",bbox_inches="tight")
    plt.close(fig)

fig,ax=canvas("1  Control: what is allowed?", "Dependencies and failure routes. A box grants no evidence that its action ran.")
for x,t,b in [(.4,"Fit and predict","training rows → model\nselection inputs → predictions"),(5.0,"Check saved result","same candidate and selection rows\nrecompute score; compare records"),(9.6,"Use checked score","only after a passing check\nprepare presentation report")]:
    box(ax,x,3.85,3.8,1.75,t,b)
arrow(ax,(4.3,4.72),(4.85,4.72));arrow(ax,(8.9,4.72),(9.45,4.72),"pass")
box(ax,.4,1.2,3.8,1.7,"Stop and preserve","a failed check cannot authorize\nuse of the score", "red")
box(ax,5,1.2,3.8,1.7,"Retain report exception","preserve predictions and ledger\nrecheck before recovery", "amber")
box(ax,9.6,1.2,3.8,1.7,"Write recovered report","reference the same prediction hash\nno additional fit required", "green")
arrow(ax,(5.6,3.72),(3.5,3.0),"check fails")
arrow(ax,(11.5,3.72),(7.8,3.0),"report fails")
arrow(ax,(8.9,2.05),(9.45,2.05),"recheck passes")
finish(fig,ax,"control-view","Analytical view of the archived workflow; not a claim of a separately frozen original plan.")

fig,ax=canvas("2  Data flow: what does the check read?", "Candidate: trial-001. The recovery workspace copied the completed run's artifacts.")
box(ax,.4,3.8,3.9,1.85,"Saved candidate artifacts","trial-001/predictions.csv\ntrial-001/RESULT.md\ntrials.csv", "green")
box(ax,.4,1.25,3.9,1.85,"Pinned task data","examples/bike-demand/source/hour.csv\nselection membership and target values\nare read by the checker", "green")
box(ax,5.05,2.5,3.8,2.15,"check_result.check","verifies row order and targets\nrecomputes MAE\ncompares ledger and result", "blue")
box(ax,9.65,2.5,3.8,2.15,"Returned score → report","RECOVERED-REPORT.md\nMAE 159.947912\nwith prediction SHA-256", "green")
arrow(ax,(4.4,4.5),(4.9,3.95));arrow(ax,(4.4,2.05),(4.9,3.1));arrow(ax,(8.95,3.55),(9.5,3.55))
finish(fig,ax,"artifact-view","The recovery CHECK.md was copied from the earlier run. The in-process recheck did not write a new CHECK.md.")

fig,ax=canvas("3  Trace: what is actually recorded?", "Order comes from the command ledger and recovery source. Absolute event timestamps were not retained.")
box(ax,.4,3.85,3.8,1.8,"Completed run: 00-03","fit/predict command: exit 0\ncheck command: exit 0\ntrial-001 score: 159.947912", "green")
box(ax,5,3.85,3.8,1.8,"Failure boundary: 03-05","copy original artifacts\ninjected report exception retained\nrecovered report not yet produced", "red")
box(ax,9.6,3.85,3.8,1.8,"Later recovery","in-process recheck returns score\nRECOVERED-REPORT.md written\nprediction hash unchanged", "green")
arrow(ax,(4.3,4.7),(4.85,4.7),"reuse")
arrow(ax,(8.9,4.7),(9.45,4.7),"later")
box(ax,.4,1.15,6.15,1.75,"Direct retained evidence","COMMANDS.md; trial-001/CHECK.md; REPORT-FAILURE.md;\nRECOVERED-REPORT.md; STRUCTURE-CHECKS.md", "gray")
box(ax,7.1,1.15,6.3,1.75,"Limits of the trace","Recovery ordering is reconstructed from program + outputs.\nNo separate recovery event journal or new fit is claimed.", "amber")
finish(fig,ax,"trace-view","A later successful repair does not mean the failed attempt already produced the recovered report.")

save("VIEWS.md", '''# Three views of one candidate's work

The completed run is `00-03/trial-001`: a constant bike-demand model with calendar features, seed 17. The later `03-05/diagnostic` workspace copied that run before injecting a report failure. Its predictions and ledger did not change during recovery. This audit reads both records without running another fit or check.

## Control view

![Allowed dependencies and failure routes](control-view.png)

This analytical plan distinguishes fitting, checking, and reporting. It is derived from the archived procedures; it is not an independently preserved, preregistered control graph. See [editable source](control-plan.mmd).

## Artifact view

![Concrete inputs and output of the recovery check](artifact-view.png)

Paths below are relative to the repository unless a prefix is stated.

| Action | Reads | Produces |
|---|---|---|
| Original fit/predict | pinned bike data, recipe and fixed split | 00-03/trial-001/predictions.csv, RESULT.md, trials.csv |
| Original check command | those predictions, result and ledger; pinned data | 00-03/trial-001/CHECK.md |
| Recovery copy | the original completed workspace | 03-05/diagnostic, including its already existing CHECK.md |
| Recovery in-process check | diagnostic/trial-001/predictions.csv and RESULT.md; diagnostic/trials.csv; pinned data | returned numeric score; **no new CHECK.md** |
| Recovery report write | returned score and prediction hash | diagnostic/RECOVERED-REPORT.md |

The checker reads pinned source targets; a stored target column alone is not its authority. The contract describes the experiment, but this particular check function does not itself consume CONTRACT.md. Do not draw a file-read edge just because a file sounds relevant.

## Trace view

![Recorded events and the separate recovery boundary](trace-view.png)

| Relative order | Evidence | Interpretation |
|---|---|---|
| 1 | 00-03 fit/predict entry in COMMANDS.md exits 0 | One original model execution completed |
| 2 | 00-03 check entry exits 0; CHECK.md passes | That saved candidate passed the supplied checker |
| 3 | recovery program copies 00-03 | Diagnostic workspace inherits these artifacts |
| 4 | REPORT-FAILURE.md records the injected exception | The attempted report did not complete normally |
| 5 | recovery program calls check_result.check; recovered report contains its score | A subsequent in-process check supports recovery |
| 6 | RECOVERED-REPORT.md records score and prediction hash | A later report was written with unchanged predictions |

The first two events are directly listed commands. Recovery event order is reconstructed from the retained program and outputs, not a separate timestamped journal. No per-event duration or process exit is invented for the in-process recovery calls. The source hashes are in [SOURCES.csv](SOURCES.csv).

## Failure audit

At the saved exception boundary, the later recheck and recovered report had not executed. They cannot be credited to the failed report attempt. The completed recovery has its own evidence. A copied CHECK.md must not be mistaken for an output emitted by that later recheck.

The injected error is a deliberate teaching failure. It is not evidence of a naturally occurring renderer outage. These artifacts support the described local sequence; they do not supply a tamper-proof event history.

## Change the plan, not the past

[The revised plan](revised-plan.mmd) adds a new MAE unit-label check before report use. It has not executed. The original data, predictions, command log, and checker output retain their hashes. No old result therefore gains a passed unit check. A new execution record would be needed to make that claim.
''')
for relative, original in identities:
    if sha(repo / relative) != original:
        raise SystemExit("Source changed during read-only inspection: " + relative)
save("PROGRESS.md", "# Author progress\n\nTwo archived traces inspected. Three separate PNG/SVG views, concrete data-flow table, failure audit, and unexecuted revised plan produced. All source hashes unchanged. Zero fits and zero workflow rechecks. Learner predictions, teach-back, and quiz untested. Historical timing and recovery event-journal limits remain explicit. Matplotlib " + matplotlib.__version__)
files = sorted(p for p in out.iterdir() if p.is_file())
save("MANIFEST.csv", "file,sha256\n" + "\n".join(p.name + "," + sha(p) for p in files))
print("Rendered three views; archived source hashes unchanged. Workspace:", out)

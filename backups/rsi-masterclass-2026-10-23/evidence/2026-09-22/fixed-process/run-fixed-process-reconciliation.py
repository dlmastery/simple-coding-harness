"""Two declared one-fit executions with five-action traces; no outer search."""
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO=Path.cwd().resolve()
OUT=REPO.parent / "rsi-work-2026-09-22-fixed-process"
TOOL=REPO / "rsi/tools/lab.py"
SOURCE=REPO / "rsi/examples/bike-demand/source/hour.csv"
CHECKER=REPO / "rsi/tools/check_result.py"
if (OUT / "STARTED.txt").exists():
    raise RuntimeError("Already started: inspect saved state instead of repeating fits")
(OUT / "STARTED.txt").write_text(datetime.now(timezone.utc).isoformat()+"\n",encoding="utf-8")
shutil.copyfile(Path(__file__),OUT / "run-fixed-process-reconciliation.py")


def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8",newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8",newline="") as handle:
        return list(csv.DictReader(handle))


def table(path,records):
    buffer=io.StringIO(newline="")
    writer=csv.DictWriter(buffer,fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    save(path,buffer.getvalue())


def require(ok,message):
    if not ok:
        raise RuntimeError(message)


source_hash=digest(SOURCE)
require(source_hash=="e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f","Source changed")
identities=[{"path":str(p),"sha256":digest(p)} for p in [SOURCE,TOOL,CHECKER,OUT/"PROCESS.md",OUT/"BASELINE-SKILL.md",OUT/"TASK.md"]]
table(OUT / "INPUT-IDENTITIES.csv",identities)
save(OUT / "ENVIRONMENT.md",f"# Environment\n\nPython: {sys.version}\nExecutable: {sys.executable}\n\n"+"\n".join(f"- {p}: {version(p)}" for p in ['numpy','pandas','scikit-learn','scipy','matplotlib'])+"\n\nExisting project environment; new empty experiment workspaces.\n")
completed=[]
for lab_id,recipe_path in [('01-02',OUT/'PROCESS.md'),('01-03',OUT/'BASELINE-SKILL.md')]:
    work=OUT/lab_id
    work.mkdir(exist_ok=False)
    fields=dict(line[2:].split(': ',1) for line in recipe_path.read_text(encoding='utf-8').splitlines() if line.startswith('- ') and ': ' in line)
    require(fields=={'Task':'bike','Model':'constant','Features':'calendar','Seed':'17','Attempts':'1'},'Unexpected declared recipe')
    save(work/'DECISION.md',f"# Instruction to action\n\nRead {recipe_path.name}, SHA256 {digest(recipe_path)}. The saved Task, Model, Features, Seed and Attempts fields supply the tool arguments. The fixed driver performs the five process actions; it is not an autonomous planner. This is author file-based instruction use in one context.\n")
    trace=[]

    def stage(name,inputs,outputs,operation):
        entry={'action':name,'inputs':inputs,'outputs':outputs,'start_utc':datetime.now(timezone.utc).isoformat(),'end_utc':'','seconds':'','status':'running'}
        trace.append(entry)
        table(work/'TRACE.csv',trace)
        start=time.perf_counter()
        try:
            operation()
            entry['status']='complete'
        except Exception as exc:
            entry['status']='failed: '+repr(exc)
            raise
        finally:
            entry['end_utc']=datetime.now(timezone.utc).isoformat()
            entry['seconds']=time.perf_counter()-start
            table(work/'TRACE.csv',trace)

    def command(label,script,args):
        command_args=[sys.executable,'-B',str(script),*map(str,args)]
        start=time.perf_counter()
        result=subprocess.run(command_args,capture_output=True,text=True,encoding='utf-8',timeout=60)
        elapsed=time.perf_counter()-start
        save(work/(label+'-command.txt'),f"Arguments: {command_args!r}\nExit: {result.returncode}\nProcess wall seconds: {elapsed}\n\n"+result.stdout+result.stderr)
        require(result.returncode==0,f"{label} failed; no automatic retry")

    def frame():
        task=(OUT/'TASK.md').read_text(encoding='utf-8')
        require('rentals per hour' in task and 'Exclude casual, registered' in task,'Task meaning changed')
        shutil.copyfile(OUT/'TASK.md',work/'TASK.md')
        save(work/'FRAME-CHECK.md','# Frame check\n\nRead the already authored task and confirmed target cnt, rentals per hour, calendar baseline, component-count exclusion and retrospective scope. No task was chosen from this run’s outcome.\n')

    def split():
        source=rows(SOURCE)
        dates=[r['dteday'] for r in source]
        train={i for i,d in enumerate(dates) if d<'2012-01-01'}
        select={i for i,d in enumerate(dates) if '2012-01-01'<=d<'2012-07-01'}
        final={i for i,d in enumerate(dates) if d>='2012-07-01'}
        require(not(train&select or train&final or select&final),'Partition overlap')
        require(train|select|final==set(range(len(dates))),'Missing rows')
        save(work/'SPLIT.md',f'# Split check before fitting\n\nTraining: {len(train)}; selection: {len(select)}; final: {len(final)}. Roles are disjoint and complete. The existing task fixed these dates before this action. No outcome-based split search. The prior inspection reports full public summaries, so no secret holdout is claimed.\n')

    stage('frame','TASK.md; data-card context','TASK.md; FRAME-CHECK.md',frame)
    stage('inspect','pinned hour.csv','DATA-REPORT.md; sample.csv; data-overview.png',lambda:command('inspect',TOOL,['inspect','--task',fields['Task'],'--workspace',work]))
    stage('split','TASK.md; source dates','SPLIT.md',split)
    fit_args=['run','--task',fields['Task'],'--workspace',work,'--model',fields['Model'],'--features',fields['Features'],'--seed',fields['Seed'],'--attempt-limit',fields['Attempts'],'--hypothesis','Reproduce the fixed training-median baseline without changing its recipe.']
    if lab_id=='01-03':
        fit_args+=['--policy',recipe_path]
    stage('fit',recipe_path.name+'; task and training data','CONTRACT.md; trials.csv; trial-001 artifacts',lambda:command('fit',TOOL,fit_args))
    stage('check','predictions; source targets; candidate registry','trial-001/CHECK.md',lambda:command('check',CHECKER,[work/'trial-001','--report',work/'trial-001/CHECK.md']))
    ledger=rows(work/'trials.csv')
    require(len(ledger)==1 and ledger[0]['status']=='ok','Wrong fit count')
    save(work/'TRACE.md','# Actual five-action trace\n\nEach row in TRACE.csv was written as running before its action and completed afterward. Frame and split are in-process checks; command logs record inspection, fit and prediction-check exit statuses and wall time. These intervals overlap their parent action intervals and must not be added twice.\n\n'+ '\n'.join(f"- {r['action']}: {r['status']}; {r['seconds']:.6f} seconds; {r['outputs']}" for r in trace)+'\n')
    save(work/'PROGRESS.md','# Progress\n\nAll five actions completed. One fit used; zero attempts remain. No final evaluation. Learner checkpoints unattempted.\n')
    completed.append(work)

old=REPO/'rsi/evidence/2026-09-20/clean-journey/01-02'
comparison=[]
for label,work in [('historical',old),*[(p.name,p) for p in completed]]:
    row=rows(work/'trials.csv')[0]
    comparison.append({'run':label,'model':row['model'],'features':row['features'],'seed':row['seed'],'score':row['score'],'fit_seconds':row['seconds'],'predictions_sha256':digest(work/'trial-001/predictions.csv'),'contract_sha256':digest(work/'CONTRACT.md')})
table(OUT/'COMPARISON.csv',comparison)
require(len({r['predictions_sha256'] for r in comparison})==1,'Prediction difference; inspect before claiming repeatability')
copy=OUT/'missing-report-copy'
shutil.copytree(completed[0],copy)
report=copy/'trial-001/RESULT.md'
require(report.resolve().is_relative_to(copy.resolve()),'Wrong teaching-copy path')
shutil.copyfile(report,OUT/'REMOVED-REPORT.md')
report.unlink()
checks={
    'original result preserved':(completed[0]/'trial-001/RESULT.md').is_file(),
    'copy result absent':not report.exists(),
    'copy predictions unchanged':digest(copy/'trial-001/predictions.csv')==digest(completed[0]/'trial-001/predictions.csv'),
    'copy successful ledger unchanged':digest(copy/'trials.csv')==digest(completed[0]/'trials.csv'),
    'one success still recorded':len(rows(copy/'trials.csv'))==1 and rows(copy/'trials.csv')[0]['status']=='ok',
    'skill snapshot matches read input':digest(completed[1]/'trial-001/POLICY-SNAPSHOT.md')==digest(OUT/'BASELINE-SKILL.md'),
}
table(OUT/'CHECKS.csv',[{'check':k,'passed':v} for k,v in checks.items()])
require(all(checks.values()),'Post-run artifact check failed')
save(OUT/'PROGRESS.md','# Progress\n\nTwo declared fits complete, one per workspace. Six child commands succeeded. Missing-report copy checked without retraining. No live process. Finish prose extension, visual review and archive; no more fits. Learner checkpoints unattempted.\n')
print('Two one-fit processes completed; matching prediction bytes; six artifact checks passed.')

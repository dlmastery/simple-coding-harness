"""Five declared fits. Separate step processes read and preserve Markdown state."""
import csv
from datetime import datetime,timezone
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO=Path.cwd().resolve()
OUT=REPO.parent/'rsi-work-2026-09-22-loop-state-feedback'
TOOL=REPO/'rsi/tools/lab.py'
CHECKER=REPO/'rsi/tools/check_result.py'


def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8',newline='\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:
        raise RuntimeError(message)


def fields(path):
    return dict(line[2:].split(': ',1) for line in path.read_text(encoding='utf-8').splitlines() if line.startswith('- ') and ': ' in line)


def rows(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8',newline='') as handle:
        return list(csv.DictReader(handle))


def table(path,records):
    buffer=io.StringIO(newline='')
    writer=csv.DictWriter(buffer,fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    save(path,buffer.getvalue())


def command(folder,label,script,args,expected=0):
    argv=[sys.executable,'-B',str(script),*map(str,args)]
    started=datetime.now(timezone.utc).isoformat()
    clock=time.perf_counter()
    result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=60)
    elapsed=time.perf_counter()-clock
    save(folder/(label+'-command.txt'),f'Arguments: {argv!r}\nStart UTC: {started}\nEnd UTC: {datetime.now(timezone.utc).isoformat()}\nExit: {result.returncode}\nExpected: {expected}\nProcess wall seconds: {elapsed}\n\n'+result.stdout+result.stderr)
    require(result.returncode==expected,f'Unexpected {label} outcome; preserve and inspect')


def retained(records):
    good=[r for r in records if r['status']=='ok']
    return min(good,key=lambda r:(float(r['score']),r['candidate']))['candidate'] if good else 'none'


def state_text(records):
    return '# Durable loop state\n\n'+f"- Spent: {len(records)}\n- Current: {records[-1]['candidate'] if records else 'none'}\n- Retained: {retained(records)}\n"


def fit(folder,recipe,hypothesis,label):
    command(folder,label+'-fit',TOOL,['run','--task',recipe['Task'],'--workspace',folder,
        '--model',recipe['Model'],'--features',recipe['Features'],'--seed',recipe['Seed'],
        '--attempt-limit',recipe['Limit'],'--hypothesis',hypothesis])
    candidate=rows(folder/'trials.csv')[-1]['candidate']
    command(folder,label+'-check',CHECKER,[folder/candidate,'--report',folder/candidate/'CHECK.md'])


def step():
    plan=fields(OUT/'LOOP.md')
    require(digest(OUT/'LOOP.md')==(OUT/'LOOP.sha256').read_text().strip(),'Loop plan changed')
    folder=OUT/'02-02'
    state=fields(folder/'STATE.md')
    records=rows(folder/'trials.csv')
    expected=fields_from_records={'Spent':str(len(records)),'Current':records[-1]['candidate'] if records else 'none','Retained':retained(records)}
    require(state==expected,'State and ledger disagree')
    count=len(records)
    if count>=int(plan['Limit']):
        save(folder/'STOP.md','# Stop\n\nRead state and ledger: three of three attempts spent. No fit requested. Retained candidate '+state['Retained']+'.\n')
        print('REFUSED: saved loop budget exhausted before another fit')
        return 2
    model=plan['Models'].split(',')[count]
    shutil.copyfile(folder/'STATE.md',folder/f'STATE-READ-{count+1}.md')
    save(folder/f'NEXT-{count+1}.md',f'# Decision before fit\n\nState SHA256: {digest(folder / "STATE.md")}\nSpent: {count}\nRead next recipe from fixed plan: {model}/{plan["Features"]}, seed {plan["Seed"]}.\nPrior retained candidate: {state["Retained"]}.\n')
    recipe={'Task':plan['Task'],'Model':model,'Features':plan['Features'],'Seed':plan['Seed'],'Limit':plan['Limit']}
    fit(folder,recipe,'Execute the next declared model under the fixed three-attempt loop.',f'step-{count+1}')
    after=rows(folder/'trials.csv')
    require(len(after)==count+1,'Unexpected attempt count')
    updated=state_text(after)
    save(folder/'STATE.md',updated)
    save(folder/f'STATE-AFTER-{count+1}.md',updated)
    print(f"Step {count+1}: current {after[-1]['candidate']}; retained {retained(after)}")
    return 0


def main():
    require(not (OUT/'STARTED.txt').exists(),'Already started; inspect and resume from evidence, do not rerun')
    save(OUT/'STARTED.txt',datetime.now(timezone.utc).isoformat()+'\n')
    shutil.copyfile(Path(__file__),OUT/'run-loop-state-feedback.py')
    paths=[OUT/'LOOP.md',OUT/'FEEDBACK.md',OUT/'DECISION-1.md',OUT/'DECISION-2.md',TOOL,CHECKER,REPO/'rsi/examples/bike-demand/source/hour.csv']
    identities=[{'path':str(p),'sha256':digest(p)} for p in paths]
    table(OUT/'INPUT-IDENTITIES.csv',identities)
    save(OUT/'LOOP.sha256',digest(OUT/'LOOP.md')+'\n')
    loop=OUT/'02-02'
    loop.mkdir(exist_ok=False)
    save(loop/'STATE.md',state_text([]))
    save(loop/'STATE-INITIAL.md',state_text([]))
    for number in range(1,4):
        command(loop,f'controller-{number}',Path(__file__),['step'])
    command(loop,'compare',TOOL,['compare','--workspace',loop])
    command(loop,'stop',Path(__file__),['step'],expected=2)
    feedback=OUT/'02-03'
    feedback.mkdir(exist_ok=False)
    for number in (1,2):
        decision=OUT/f'DECISION-{number}.md'
        require(digest(decision)==identities[number+1]['sha256'],'Decision changed before use')
        require(digest(OUT/'FEEDBACK.md')==identities[1]['sha256'],'Feedback changed')
        recipe=fields(decision)
        shutil.copyfile(decision,feedback/f'DECISION-READ-{number}.md')
        save(feedback/f'FEEDBACK-USE-{number}.md',f'# Input read before fit\n\nFeedback SHA256: {digest(OUT / "FEEDBACK.md")}\nDecision SHA256: {digest(decision)}\nThe saved Features field supplies {recipe["Features"]}; the other recipe fields remain fixed. This is an author-guided adapter, not autonomous diagnosis.\n')
        fit(feedback,recipe,'Test the weather-feature hypothesis recorded before fitting.',f'candidate-{number}')
    command(feedback,'compare',TOOL,['compare','--workspace',feedback])
    loop_rows=rows(loop/'trials.csv')
    feedback_rows=rows(feedback/'trials.csv')
    checks={
        'three loop fits':len(loop_rows)==3,
        'two feedback fits':len(feedback_rows)==2,
        'loop final state agrees':fields(loop/'STATE.md')=={'Spent':'3','Current':'trial-003','Retained':retained(loop_rows)},
        'last candidate not automatically retained':retained(loop_rows)=='trial-002',
        'changed feature group only':[(r['model'],r['features'],r['seed']) for r in feedback_rows]==[('linear','calendar','17'),('linear','all','17')],
        'loop state versions retained':all((loop/f'STATE-READ-{i}.md').exists() and (loop/f'STATE-AFTER-{i}.md').exists() for i in range(1,4)),
        'frozen inputs unchanged':all(digest(Path(r['path']))==r['sha256'] for r in identities),
        'no final evaluation':not any((p/'FINAL-LOCK.md').exists() for p in [loop,feedback]),
    }
    table(OUT/'CHECKS.csv',[{'check':k,'passed':v} for k,v in checks.items()])
    require(all(checks.values()),'Post-run invariant failed')
    save(OUT/'PROGRESS.md','# Progress\n\nAll five allocated fits and five prediction checks completed. Loop stop refused without another fit. State versions and pre-fit feedback/decision copies retained. No live processes or further fits allowed. Learner checkpoints unattempted.\n')
    print('Five fits completed; five prediction checks and eight invariants pass; no final evaluation.')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='step':
        raise SystemExit(step())
    main()

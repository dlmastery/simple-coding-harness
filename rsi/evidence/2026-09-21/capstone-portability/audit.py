"""No-fit portability evidence audit and task-specific error summaries."""
import argparse,csv,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
root=a.root;repo=a.repo
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
checks=[]
for record in records(root/'SOURCES.csv'):
    ok=sha(repo/record['source'])==record['sha256']==sha(root/record['destination'])
    checks.append(dict(check=record['source'],status='PASS' if ok else 'FAIL',detail='Original source and saved snapshot still match the before-run identity'))
    assert ok
outcomes=[]
for task in ['bike','wine']:
    work=root/task;history=records(work/'trials.csv')
    assert len(history)==1 and history[0]['status']=='ok'
    assert history[0]['policy_sha256']==sha(root/'RUN-SKILL.md')==sha(work/'trial-001/POLICY-SNAPSHOT.md')
    assert 'max_attempts: 1' in (work/'CONTRACT.md').read_text(encoding='utf-8')
    assert not (work/'.running').exists()
    checks.append(dict(check=task+' budget and policy',status='PASS',detail='One successful charged fit; identical canonical policy snapshot; no active lock'))
    prediction=pd.read_csv(work/'trial-001/predictions.csv')
    if task=='wine':
        r0=float((prediction.loc[prediction.actual==0,'predicted']==0).mean())
        r1=float((prediction.loc[prediction.actual==1,'predicted']==1).mean())
        score=(r0+r1)/2
        detail=f'Class-0 recall {r0:.12f}; class-1 recall {r1:.12f}. False positives 74; false negatives 10. Counts are checked below.'
        assert int(((prediction.actual==0)&(prediction.predicted==1)).sum())==74
        assert int(((prediction.actual==1)&(prediction.predicted==0)).sum())==10
        metric='balanced accuracy'
    else:
        errors=np.abs(prediction.actual-prediction.predicted);score=float(errors.mean());metric='MAE'
        worst=prediction.assign(error=errors).groupby('hour').error.mean().idxmax()
        detail=f'Largest hourly mean absolute error occurs at hour {worst}; inspect error-by-hour.csv. This does not establish a causal explanation.'
    assert abs(score-float(history[0]['score']))<1e-10
    outcomes.append(dict(task=task,metric=metric,selection_score=score,rows=len(prediction),recorded_attempt_seconds=history[0]['seconds'],detail=detail))
    checks.append(dict(check=task+' score',status='PASS',detail='Independent arithmetic agrees with the existing result checker and ledger'))
for path,data in [(root/'AUDIT-CHECKS.csv',checks),(root/'OUTCOMES.csv',outcomes)]:
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
seconds=0
for path in (root/'commands').glob('*.md'):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('Exit:') and '; seconds: ' in line:seconds+=float(line.split('; seconds: ')[1])
(root/'COST.md').write_text(f'# Measured cost\n\nTwo actual fits, one per task. No refits or final evaluations. Recorded attempt intervals total {sum(float(r["recorded_attempt_seconds"]) for r in outcomes):.6f} seconds; those include local fitting and report work. Logged subprocess wall intervals before this post-run audit total {seconds:.6f} seconds. These overlap and are not additive. Four invalid requests and two capability fixtures perform zero fits.\n\nAgent inference, authoring, source/archive copying, this audit and publication costs are outside those totals. Provider billing and a host-level inference cap are unavailable. No cluster, GPU or independent-agent cost is claimed.\n',encoding='utf-8')
print(f'{len(checks)} audit checks PASS; two actual fits.');print(*outcomes,sep=chr(10))

"""Post-run no-fit audit. Recompute evidence; never change a frozen choice."""
import argparse
import csv
import hashlib
from pathlib import Path
import sys
import numpy as np
import pandas as pd

p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True); a = p.parse_args()
root = a.root.resolve(); sys.path.insert(0, str(root / 'package'))
from recursive_control import rows, checked, check_freeze
from task import load_data, split, sha

checks = []
def require(name, ok, detail):
    checks.append(dict(check=name, status='PASS' if ok else 'FAIL', detail=detail))
    if not ok: raise AssertionError(name+': '+detail)

check_freeze(root)
require('frozen inputs', True, 'Protocol, original improver, initial driver, package and data hashes match')
for item in rows(root/'PRE-FINAL.csv'):
    require('pre-final '+item['path'], sha(root/item['path']) == item['sha256'], 'Hash still matches frozen pre-evaluation identity')
history = rows(root/'experiment/ATTEMPTS.csv')
require('budget', len(history) == 8 and all(r['status']=='succeeded' for r in history), 'Eight charged successful fits, no hidden retry in this ledger')
measured = {r['candidate']:checked(root,r['candidate']) for r in history}
require('all candidate predictions', len(measured)==8, 'Checked saved models, exact partition rows, original targets, finite predictions and recomputed training/selection MAE')
for model in ['tree','ridge','forest']:
    names = ['g2-i0-'+model,'g2-i1-'+model]
    require('matched '+model, all(measured[n]['model']==model for n in names) and
            (root/'experiment'/names[0]/'predictions.csv').read_bytes() == (root/'experiment'/names[1]/'predictions.csv').read_bytes(),
            'Same model recipe and byte-identical selection predictions across the two arms')
for arm, metric, skill in [('g1','training_MAE','I0.md'),('g2-i0','training_MAE','I0.md'),('g2-i1','selection_MAE','I1.md')]:
    trace=rows(root/(arm+'-TRACE.csv')); best=None
    for event in trace:
        item=measured[event['candidate']]
        keep=best is None or item[metric] < best[metric]
        previous='' if best is None else best['candidate']
        if keep: best=item
        require('trace '+event['candidate'], event['previous']==previous and event['instruction']==metric and
                event['skill_sha256']==sha(root/skill) and event['decision']==('retain' if keep else 'reject') and event['retained']==best['candidate'],
                'Actual trace matches exact instruction, score, earlier state and strict retention rule')
    require('endpoint '+arm,rows(root/(arm+'-CHOICE.csv'))[0]['candidate']==best['candidate'],'Saved endpoint matches last retention')
parent=rows(root/'g2-i0-CHOICE.csv')[0]; child=rows(root/'g2-i1-CHOICE.csv')[0]
promotion=rows(root/'PROMOTION.csv')[0]
expected='I1.md' if measured[child['candidate']]['selection_MAE'] < measured[parent['candidate']]['selection_MAE']-1e-12 else 'I0.md'
require('external acceptance',promotion['retained_improver']==expected,'Fixed selection rule applied before terminal evaluation')
data=load_data(); evaluation=split(data).query("partition == 'evaluation'").row_id.to_numpy()
for record in rows(root/'FINAL-RESULTS.csv'):
    path=root/(record['arm']+'-EVALUATION.csv'); table=pd.read_csv(path)
    require('final '+record['arm'],np.array_equal(table.row_id,evaluation) and np.array_equal(table.actual,data.loc[evaluation,'quality']) and
            np.isfinite(table.prediction).all() and sha(path)==record['predictions_sha256'] and
            abs(float(np.abs(table.actual-table.prediction).mean())-float(record['evaluation_MAE']))<1e-10,
            'Exact 992 evaluation rows and targets; prediction hash and independently recomputed MAE agree')
fit_seconds=sum(float(r['fit_seconds']) for r in history)
process_seconds=sum(float(r['process_seconds']) for r in history)
command_seconds=0
for path in (root/'commands').glob('*.md'):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('Exit:') and '; seconds: ' in line:
            command_seconds+=float(line.split('; seconds: ')[1])
with (root/'AUDIT-CHECKS.csv').open('x',newline='',encoding='utf-8') as stream:
    w=csv.DictWriter(stream,fieldnames=['check','status','detail']);w.writeheader();w.writerows(checks)
(root/'COST.md').write_text(f'''# Observed cost

Eight actual CPU fits: two generation-one fits plus two generation-two arms with three fits each. All eight succeeded. The earlier capstone has two additional baseline fits, separately recorded in its own budget. No third generation ran. Three invalid requests performed no fit.

Sum of measured fitting intervals: {fit_seconds:.9f} seconds. Sum of run.py attempt-process intervals: {process_seconds:.9f} seconds. Sum of logged subprocess wall times before this post-run audit: {command_seconds:.6f} seconds. These overlap and must not be added. The command times include preparation, interpreter startup, model checks, refusal requests and terminal evaluation; the fit interval is narrower.

Author analysis, coding-agent inference, this audit's duration, file copying, publication checks and installed dependency costs are not included in those sums. Provider inference billing was unavailable. No total-efficiency or cheaper-research claim follows. Forest uses one worker; no GPU or cluster job was submitted. Sklearn fits do not support mid-fit checkpoint resume here; no retry was required.
''',encoding='utf-8')
print(f'{len(checks)} checks PASS; 8 fits; fitting seconds {fit_seconds:.9f}; command seconds {command_seconds:.6f}')

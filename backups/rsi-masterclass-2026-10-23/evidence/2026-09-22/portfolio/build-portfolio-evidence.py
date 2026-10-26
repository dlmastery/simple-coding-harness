"""Trace existing records for teaching. Performs zero fits or model inference."""
import argparse,csv,hashlib,time,sys,platform
from pathlib import Path
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
repo=a.repo.resolve();out=a.output.resolve();start=time.perf_counter()
out.mkdir(exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def readcsv(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def write(name,rows):
    with (out/name).open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
base=repo/'rsi/evidence/2026-09-21'
groups={
 'capstone-harness':['package/TASK.md','package/DATA-CARD.md','package/data/winequality-white.csv',
                     'package/WORKFLOW.md','export/experiment/baseline/predictions.csv'],
 'capstone-recursion':['PROTOCOL.md','I0.md','I1.md','CHANGE-PROPOSAL.md','g1-TRACE.csv','g1-TASK-SKILL.md',
                       'g2-i0-START.md','g2-i1-START.md','g2-i0-TRACE.csv','g2-i1-TRACE.csv','PROMOTION.csv','PRE-FINAL.csv',
                       'FINAL-RESULTS.csv','COST.md','CLAIM-AUDIT.md','experiment/SPLIT.csv',
                       'experiment/g2-i0-tree/predictions.csv','experiment/g2-i1-forest/predictions.csv'],
 'meta-skills':['prerequisites/parent-milliseconds/RESULT.md','10-16/target/RESULT.md','10-16/second/RESULT.md',
                'skills/TASK-SKILL-v0.md','skills/TASK-SKILL-v1.md','skills/META-SKILL-v0.md','COST.md']}
identities=[]
for group,names in groups.items():
    manifest={r['path']:r['sha256'] for r in readcsv(base/group/'MANIFEST.csv')}
    for name in names:
        path=base/group/name
        value=sha(path)
        if manifest.get(name)!=value:raise AssertionError('Original manifest mismatch: '+str(path))
        identities.append(dict(path=path.relative_to(repo).as_posix(),sha256=value,status='PASS'))
write('CHECKED-IDENTITIES.csv',identities)
data=pd.read_csv(base/'capstone-harness/package/data/winequality-white.csv',sep=';')
row_id=26;sample=data.iloc[row_id]
split=pd.read_csv(base/'capstone-recursion/experiment/SPLIT.csv').set_index('row_id').loc[row_id]
assert split['partition']=='selection'
write('ROW-26.csv',[dict(field=k,value=v,role='target for checking only' if k=='quality' else 'model input') for k,v in sample.items()])
results=[]
for arm,candidate in [('original rule','g2-i0-tree'),('revised rule','g2-i1-forest')]:
    prediction=pd.read_csv(base/'capstone-recursion/experiment'/candidate/'predictions.csv').set_index('row_id').loc[row_id]
    assert prediction.actual==sample.quality
    results.append(dict(row_id=row_id,partition=split['partition'],group=split['group'],arm=arm,candidate=candidate,
                        target=prediction.actual,prediction=prediction.prediction,absolute_error=abs(prediction.actual-prediction.prediction)))
write('ROW-PREDICTIONS.csv',results)
start0=(base/'capstone-recursion/g2-i0-START.md').read_bytes();start1=(base/'capstone-recursion/g2-i1-START.md').read_bytes()
assert start0==start1==(base/'capstone-recursion/g1-TASK-SKILL.md').read_bytes()
trace=readcsv(base/'capstone-recursion/g2-i1-TRACE.csv')
assert all(r['instruction']=='selection_MAE' and r['skill_sha256']==sha(base/'capstone-recursion/I1.md') for r in trace)
assert trace[-1]['retained']=='g2-i1-forest'
checks=[dict(check='source manifest identities',status='PASS',detail=str(len(identities))+' previously sealed records match'),
        dict(check='prediction row',status='PASS',detail='Zero-based row 26 is selection; original quality target matches both predictions'),
        dict(check='matched start',status='PASS',detail='Both generation-two starts equal the saved tree recipe bytes'),
        dict(check='later rule use',status='PASS',detail='I1 trace identifies the saved file and selection_MAE instruction; endpoint forest')]
write('CHECKS.csv',checks)
(out/'RUN.md').write_text(f'# Evidence assembly check\n\nPython {sys.version}; {platform.platform()}\n\nChecked {len(identities)} source identities. Read one existing data row and two saved prediction rows. Zero fits and zero model inference. Elapsed script seconds before writing this record: {time.perf_counter()-start:.9f}. File copying, authoring, inference and publication work are additional and not measured here.\n',encoding='utf-8')
print(f'{len(identities)} original manifest identities PASS; four evidence checks PASS; zero fits.');print(*results,sep=chr(10))

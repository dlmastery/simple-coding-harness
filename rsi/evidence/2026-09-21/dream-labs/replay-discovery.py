"""Read-only classroom node-order replay: no training or subprocess dependency."""
import argparse
import csv
from pathlib import Path
import time

parser=argparse.ArgumentParser()
parser.add_argument('--tree',required=True,type=Path)
parser.add_argument('--policy',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
if args.output.exists():raise SystemExit('Preserve existing replay')
args.output.mkdir(parents=True)
start=time.perf_counter()
with args.tree.open(encoding='utf-8',newline='') as stream:records={r['node']:r for r in csv.DictReader(stream)}
policy=dict(line.split(': ',1) for line in args.policy.read_text().splitlines() if ': ' in line)
limit=int(policy['Attempt units']);seen={'R'};spent=0;best=None;historical=0.;trace=[]
for node in policy['Order'].split():
    if spent>=limit:break
    record=records.get(node)
    if not record or record['parent'] not in seen or record['status']!='ok' or not record['mae']:
        trace.append([node,'unknown','','','not a supported measured continuation']);break
    seen.add(node);spent+=1;score=float(record['mae']);historical+=float(record['fit_seconds'])
    if best is None or score<best[1]:best=(node,score)
    trace.append([node,'revealed',record['mae'],record['fit_seconds'],record['result']])
elapsed=time.perf_counter()-start
with (args.output/'TRACE.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.writer(stream,lineterminator='\n');writer.writerow(['node','status','mae','historical_fit_seconds','source']);writer.writerows(trace)
(args.output/'RESULT.md').write_text(f'# Replay result\n\nBest node: {best[0] if best else "unknown"}\nBest MAE: {best[1] if best else "unknown"}\nRepresented attempts: {spent}\nHistorical fit seconds represented: {historical:.9f}\nReplay computation seconds: {elapsed:.9f}\nActual new fits: 0\n\nRepresented attempts are reused outcomes, not measured counterfactual savings. Replay time excludes process startup, proposal generation, and agent inference.\n',encoding='utf-8',newline='\n')
print((args.output/'RESULT.md').read_text())

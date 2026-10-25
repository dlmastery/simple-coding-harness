"""Check saved screen predictions without fitting or importing the model runner."""
import argparse
import csv
import math
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--candidate',type=Path,required=True)
a=p.parse_args()
def rows(path):
    with path.open(newline='',encoding='utf-8') as stream:return list(csv.DictReader(stream))
source=rows(a.source)
expected=[i for i,r in enumerate(source) if '2012-01-01' <= r['dteday'] < '2012-02-01']
training=[i for i,r in enumerate(source) if '2011-01-01' <= r['dteday'] < '2011-04-01']
predictions=rows(a.candidate/'predictions.csv')
assert [int(r['row']) for r in predictions]==expected
assert [int(r['row']) for r in rows(a.candidate/'SELECTION-ROWS.csv')]==expected
assert [int(r['row']) for r in rows(a.candidate/'TRAIN-ROWS.csv')]==training
errors=[]
for record in predictions:
    target=float(source[int(record['row'])]['cnt'])
    predicted=float(record['predicted'])
    assert target==float(record['actual']) and math.isfinite(predicted) and predicted>=0
    errors.append(abs(target-predicted))
score=math.fsum(errors)/len(errors)
fields=dict(line.split(': ',1) for line in (a.candidate/'RESULT.md').read_text().splitlines() if ': ' in line)
assert abs(score-float(fields['Selection MAE']))<1e-8
(a.candidate/'CHECK.md').write_text(f'# Separate screening check\n\nPASS: row membership, source targets, finite nonnegative predictions, and MAE agree.\nRecomputed MAE: {score:.12f}\n\nThis check does not prove that the claimed model generated the predictions or create evaluator secrecy.\n',encoding='utf-8',newline='\n')
print(f'Screen check passed: {score:.12f}')

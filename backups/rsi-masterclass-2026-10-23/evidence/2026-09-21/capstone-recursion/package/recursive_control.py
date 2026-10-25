"""Generated, fixed controller for the separately budgeted 11.02 extension.

Only trusted, locally generated joblib files are loaded. This is an author
walkthrough controller, not an autonomous proposer or a security boundary.
"""
import argparse
import csv
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from task import ROOT, Refusal, identity, load_data, split, sha, FEATURES
from evaluate import evaluate


def rows(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def write(path, records):
    if not records:
        raise Refusal('No records to write')
    with Path(path).open('x', newline='', encoding='utf-8') as stream:
        w = csv.DictWriter(stream, fieldnames=list(records[0]))
        w.writeheader(); w.writerows(records)


def check_freeze(root):
    for item in rows(root / 'FROZEN.csv'):
        if sha(root / item['path']) != item['sha256']:
            raise Refusal('Frozen input changed: ' + item['path'])


def checked(root, candidate):
    work = root / 'experiment'; folder = work / candidate
    score = evaluate(folder, work)
    report = pd.read_csv(folder / 'metrics.csv').iloc[0]
    if report.model_sha256 != sha(folder / 'model.joblib') or report.training_predictions_sha256 != sha(folder / 'training-predictions.csv'):
        raise Refusal('Saved model or training predictions changed')
    data = load_data(); partitions = split(data)
    train = partitions.query("partition == 'train'").row_id.to_numpy()
    table = pd.read_csv(folder / 'training-predictions.csv')
    if list(table.columns) != ['row_id', 'actual', 'prediction'] or not np.array_equal(table.row_id, train):
        raise Refusal('Training prediction rows or schema changed')
    if not np.array_equal(table.actual, data.loc[train, 'quality']) or not np.isfinite(table.prediction).all():
        raise Refusal('Training targets or predictions invalid')
    measured = float(np.abs(table.actual-table.prediction).mean())
    if abs(measured-report.training_MAE) > 1e-10:
        raise Refusal('Training score does not match predictions')
    model = joblib.load(folder / 'model.joblib')
    selection = pd.read_csv(folder / 'predictions.csv')
    for expected, ids in [(table.prediction, train), (selection.prediction, selection.row_id.to_numpy())]:
        actual = model.predict(data.loc[ids, FEATURES])
        if not np.allclose(actual, expected, rtol=0, atol=1e-10):
            raise Refusal('Saved model differs from recorded predictions')
    return dict(candidate=candidate, model=report.model, training_MAE=measured, selection_MAE=score)


def select(root, phase, skill, candidates):
    check_freeze(root)
    if (root / 'experiment/FINAL-LOCK.md').exists():
        raise Refusal('Experiment closed')
    if phase not in ['g1', 'g2-i0', 'g2-i1']:
        raise Refusal('Only two declared generations are allowed')
    path = root / skill
    if skill == 'I1.md':
        item = rows(root / 'CHILD-FROZEN.csv')[0]
        if item['path'] != skill or sha(path) != item['sha256']:
            raise Refusal('Candidate improver changed')
    elif skill != 'I0.md':
        raise Refusal('Unknown improver')
    text = path.read_text(encoding='utf-8')
    fields = [line.removeprefix('Rank candidates by: ') for line in text.splitlines() if line.startswith('Rank candidates by: ')]
    if len(fields) != 1 or fields[0] not in ['training_MAE', 'selection_MAE']:
        raise Refusal('Unsupported ranking instruction')
    field = fields[0]; best = None; trace = []
    for candidate in candidates:
        item = checked(root, candidate)
        accepted = best is None or item[field] < best[field]
        previous = '' if best is None else best['candidate']
        if accepted:
            best = item
        trace.append(dict(phase=phase, skill=skill, skill_sha256=sha(path), instruction=field,
                          candidate=candidate, previous=previous, training_MAE=item['training_MAE'],
                          selection_MAE=item['selection_MAE'], decision='retain' if accepted else 'reject', retained=best['candidate']))
    write(root / (phase+'-TRACE.csv'), trace)
    write(root / (phase+'-CHOICE.csv'), [best])
    (root / (phase+'-TASK-SKILL.md')).write_text('# Retained prediction recipe\n\nModel: '+best['model']+'\nInputs: all eleven permitted lab inputs\nTraining: fixed grouped training partition\nMetric: MAE\n', encoding='utf-8')
    print(f'{phase}: {skill} ({field}) retained {best["candidate"]}; selection MAE {best["selection_MAE"]:.12f}')


def freeze_decision(root):
    check_freeze(root)
    if (root / 'PRE-FINAL.csv').exists():
        raise Refusal('Decision already frozen')
    if len(rows(root / 'experiment/ATTEMPTS.csv')) != 8:
        raise Refusal('Exactly eight charged attempts required')
    if (root/'g2-i0-START.md').read_bytes() != (root/'g1-TASK-SKILL.md').read_bytes() or (root/'g2-i1-START.md').read_bytes() != (root/'g1-TASK-SKILL.md').read_bytes():
        raise Refusal('Arms did not start from identical task-skill bytes')
    choices = [rows(root / (arm+'-CHOICE.csv'))[0] for arm in ['g2-i0','g2-i1']]
    scores = [checked(root, r['candidate']) for r in choices]
    promoted = scores[1]['selection_MAE'] < scores[0]['selection_MAE']-1e-12
    write(root / 'PROMOTION.csv', [dict(retained_improver='I1.md' if promoted else 'I0.md',
          decision='accept' if promoted else 'reject', external_metric='selection_MAE',
          parent_score=scores[0]['selection_MAE'], child_score=scores[1]['selection_MAE'])])
    protected = ['I0.md','I1.md','CHILD-FROZEN.csv','CHANGE-PROPOSAL.md','PROMOTION.csv',
                 'g1-TASK-SKILL.md','g2-i0-START.md','g2-i1-START.md', 'experiment/ATTEMPTS.csv']
    for arm, choice in zip(['g2-i0','g2-i1'], choices):
        protected += [arm+'-CHOICE.csv',arm+'-TRACE.csv',arm+'-TASK-SKILL.md']
        protected += [f'experiment/{choice["candidate"]}/{name}' for name in ['model.joblib','predictions.csv','training-predictions.csv','metrics.csv']]
    write(root / 'PRE-FINAL.csv', [dict(path=p,sha256=sha(root/p)) for p in protected])
    print('Frozen external decision: '+('accept I1' if promoted else 'retain I0')+'. Final evaluation remains unopened.')


def final(root):
    check_freeze(root)
    for item in rows(root / 'PRE-FINAL.csv'):
        if sha(root / item['path']) != item['sha256']:
            raise Refusal('Pre-final artifact changed: '+item['path'])
    lock = root / 'experiment/FINAL-LOCK.md'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write('# Final closure\n\nTerminal evaluation admitted. No more fits or selection changes.\n')
    data = load_data(); ids = split(data).query("partition == 'evaluation'").row_id.to_numpy()
    result = []
    for arm in ['g2-i0','g2-i1']:
        choice = rows(root / (arm+'-CHOICE.csv'))[0]
        checked(root, choice['candidate'])
        folder = root / 'experiment' / choice['candidate']
        model = joblib.load(folder / 'model.joblib')
        predictions = model.predict(data.loc[ids, FEATURES])
        if not np.isfinite(predictions).all():
            raise Refusal('Non-finite evaluation predictions')
        table = pd.DataFrame(dict(row_id=ids,actual=data.loc[ids,'quality'].to_numpy(),prediction=predictions))
        table.to_csv(root / (arm+'-EVALUATION.csv'), index=False)
        score = float(np.abs(table.actual-table.prediction).mean())
        result.append(dict(arm=arm,candidate=choice['candidate'],evaluation_MAE=score,rows=len(table),predictions_sha256=sha(root/(arm+'-EVALUATION.csv'))))
    write(root / 'FINAL-RESULTS.csv', result)
    print(json.dumps(result))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['select','freeze','final']); p.add_argument('--root',type=Path,required=True)
    p.add_argument('--phase'); p.add_argument('--skill'); p.add_argument('--candidates',nargs='+')
    a = p.parse_args()
    try:
        if a.action == 'select': select(a.root,a.phase,a.skill,a.candidates)
        elif a.action == 'freeze': freeze_decision(a.root)
        else: final(a.root)
    except (Refusal, OSError, ValueError, KeyError) as exc:
        print('REFUSED: '+str(exc)); raise SystemExit(2)

"""Generated bounded CPU runner. The coding agent operates this interface."""
import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from task import ROOT, Refusal, load_data, split, sha, identity, validate_features, METRIC

FIELDS = ['candidate', 'model', 'features', 'status', 'fit_seconds', 'process_seconds', 'error']


def write_rows(path, rows, fields):
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def prepare(work, budget):
    if work.exists():
        raise Refusal('Experiment exists; preserve it and read its progress')
    if not 1 <= budget <= 8:
        raise Refusal('Budget must be 1 to 8 and within the separately declared lab total')
    data = load_data(); partitions = split(data)
    work.mkdir(parents=True); partitions.to_csv(work / 'SPLIT.csv', index=False)
    contract = {'task': 'white-wine-quality-regression-v1', 'metric': METRIC, 'budget': str(budget),
                'package_sha256': identity(), 'data_sha256': sha(ROOT / 'data/winequality-white.csv'),
                'split_sha256': sha(work / 'SPLIT.csv')}
    write_rows(work / 'CONTRACT.csv', [{'key': k, 'value': v} for k, v in contract.items()], ['key', 'value'])
    write_rows(work / 'ATTEMPTS.csv', [], FIELDS)
    counts = partitions.groupby('partition').size()
    report = '# Data inspection\n\n' + f'Rows: {len(data)}. Numeric inputs: 11. Missing cells: {int(data.isna().sum().sum())}.\n\n'
    report += '\n'.join(f'- {key}: {value} rows' for key, value in counts.items())
    report += f'\n\nDistinct input groups: {partitions.group.nunique()}. Repeated-input extra rows: {len(data)-partitions.group.nunique()}. No group crosses partitions.\n'
    report += '\nOnly partition counts and training-target distribution are inspected here; no selection or evaluation target summary is used to choose a split.\n'
    (work / 'DATA-REPORT.md').write_text(report, encoding='utf-8')
    train_ids = partitions.query("partition == 'train'").row_id
    data.loc[train_ids, 'quality'].value_counts().sort_index().to_csv(work / 'TRAIN-TARGET-COUNTS.csv')
    (work / 'PROGRESS.md').write_text(f'# Progress\n\nPrepared; zero of {budget} attempts admitted. Final evaluation unused.\n', encoding='utf-8')
    print(f'Prepared {len(data)} rows, {partitions.group.nunique()} input groups, budget {budget}.')


def run(args):
    work = args.workspace.resolve()
    if args.metric != METRIC:
        raise Refusal('Metric is frozen to MAE')
    chosen = validate_features(args.features)
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', args.candidate):
        raise Refusal('Invalid candidate identifier')
    contract = pd.read_csv(work / 'CONTRACT.csv', dtype=str).set_index('key').value.to_dict()
    if contract['package_sha256'] != identity() or contract['metric'] != METRIC:
        raise Refusal('Scientific package changed; use the frozen version')
    if sha(work / 'SPLIT.csv') != contract['split_sha256']:
        raise Refusal('Split changed')
    data = load_data(); partitions = split(data)
    if not pd.read_csv(work / 'SPLIT.csv').equals(partitions):
        raise Refusal('Saved split does not match fixed grouping rule')
    if (work / 'FINAL-LOCK.md').exists():
        raise Refusal('Experiment is closed by final evaluation')
    lock = work / 'RUNNING.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise Refusal('An attempt is active or interrupted; reconcile the saved lock first')
    with os.fdopen(fd, 'w') as stream:
        stream.write(f'pid={os.getpid()}\ncandidate={args.candidate}\n')
    try:
        with (work / 'ATTEMPTS.csv').open(newline='', encoding='utf-8') as stream:
            history = list(csv.DictReader(stream))
        if len(history) >= int(contract['budget']):
            raise Refusal('Attempt budget exhausted; no fit admitted')
        if (work / args.candidate).exists() or any(r['candidate'] == args.candidate for r in history):
            raise Refusal('Candidate already exists')
        destination = work / args.candidate; destination.mkdir()
        record = dict(candidate=args.candidate, model=args.model, features='|'.join(chosen), status='running', fit_seconds='', process_seconds='', error='')
        history.append(record); write_rows(work / 'ATTEMPTS.csv', history, FIELDS)
        started = time.perf_counter()
        try:
            train = partitions.query("partition == 'train'").row_id.to_numpy()
            selection = partitions.query("partition == 'selection'").row_id.to_numpy()
            models = {'median': DummyRegressor(strategy='median'), 'ridge': make_pipeline(StandardScaler(), Ridge(alpha=10)),
                      'tree': DecisionTreeRegressor(random_state=11001),
                      'forest': RandomForestRegressor(n_estimators=40, min_samples_leaf=5, random_state=11001, n_jobs=1)}
            model = models[args.model]
            fit_start = time.perf_counter(); model.fit(data.loc[train, chosen], data.loc[train, 'quality']); fit_seconds = time.perf_counter()-fit_start
            predictions = model.predict(data.loc[selection, chosen]); train_pred = model.predict(data.loc[train, chosen])
            table = pd.DataFrame({'row_id': selection, 'actual': data.loc[selection, 'quality'].to_numpy(), 'prediction': predictions})
            table.to_csv(destination / 'predictions.csv', index=False)
            metrics = {'candidate': args.candidate, 'model': args.model, 'features': record['features'], 'metric': METRIC,
                       'training_MAE': float(np.abs(data.loc[train, 'quality'].to_numpy()-train_pred).mean()),
                       'selection_MAE': float(np.abs(table.actual-table.prediction).mean()), 'fit_seconds': fit_seconds,
                       'predictions_sha256': sha(destination / 'predictions.csv')}
            pd.DataFrame([metrics]).to_csv(destination / 'metrics.csv', index=False)
            record.update(status='succeeded', fit_seconds=fit_seconds)
        except BaseException as exc:
            record.update(status='failed', error=f'{type(exc).__name__}: {exc}'); raise
        finally:
            record['process_seconds'] = time.perf_counter()-started
            write_rows(work / 'ATTEMPTS.csv', history, FIELDS)
            (work / 'PROGRESS.md').write_text(f'# Progress\n\n{len(history)} of {contract["budget"]} attempts charged. Latest: {args.candidate}, {record["status"]}. Final evaluation unused.\n', encoding='utf-8')
        from evaluate import evaluate
        try:
            score = evaluate(destination, work)
        except Exception as exc:
            record.update(status='invalid-output', error=f'{type(exc).__name__}: {exc}')
            write_rows(work / 'ATTEMPTS.csv', history, FIELDS)
            (work / 'PROGRESS.md').write_text(f'# Progress\n\n{len(history)} of {contract["budget"]} attempts charged. Latest output check failed; preserve this candidate.\n', encoding='utf-8')
            raise
        (destination / 'CHECK.md').write_text(f'# Selection check\n\nPASS: recomputed MAE {score:.12f}.\n', encoding='utf-8')
        print(f'PASS {args.candidate}: selection MAE {score:.12f}; charged attempts {len(history)}.')
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--workspace', type=Path, required=True); p.add_argument('--budget', type=int, required=True)
    p = sub.add_parser('run'); p.add_argument('--workspace', type=Path, required=True); p.add_argument('--candidate', required=True)
    p.add_argument('--model', choices=['median', 'ridge', 'tree', 'forest'], required=True); p.add_argument('--features', default='all'); p.add_argument('--metric', default=METRIC)
    args = parser.parse_args()
    try:
        if args.action == 'prepare': prepare(args.workspace.resolve(), args.budget)
        else: run(args)
    except (Refusal, OSError, ValueError, KeyError) as exc:
        print('REFUSED: ' + str(exc)); sys.exit(2)

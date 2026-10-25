"""Persist negative cases derived from an actual baseline; no extra model fits."""
import argparse
import csv
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
import run
from evaluate import evaluate
from task import Refusal


def main(baseline, output):
    if output.exists():
        raise Refusal('Preserve earlier guard evidence')
    output.mkdir(parents=True)
    cases = []
    mutations = ['false-summary', 'wrong-row', 'wrong-target', 'nonfinite', 'wrong-metric', 'wrong-recipe', 'split-change']
    for name in mutations:
        work = output / name; work.mkdir()
        for f in ['CONTRACT.csv', 'SPLIT.csv', 'ATTEMPTS.csv']:
            shutil.copyfile(baseline / f, work / f)
        shutil.copytree(baseline / 'baseline', work / 'baseline')
        report = pd.read_csv(work / 'baseline/metrics.csv')
        predictions = pd.read_csv(work / 'baseline/predictions.csv')
        if name == 'false-summary': report.loc[0, 'selection_MAE'] = 0.0
        elif name == 'wrong-row': predictions.loc[0, 'row_id'] = -1
        elif name == 'wrong-target': predictions.loc[0, 'actual'] = -100
        elif name == 'nonfinite': predictions.loc[0, 'prediction'] = float('inf')
        elif name == 'wrong-metric': report.loc[0, 'metric'] = 'accuracy'
        elif name == 'wrong-recipe': report.loc[0, 'model'] = 'tree'
        elif name == 'split-change':
            with (work / 'SPLIT.csv').open('a') as stream: stream.write('99999,fake,selection\n')
        if name in ['wrong-row', 'wrong-target', 'nonfinite']:
            predictions.to_csv(work / 'baseline/predictions.csv', index=False)
            # Rehash the bad file so row/target/finiteness checks, not stale hash alone, must catch it.
            report.loc[0, 'predictions_sha256'] = run.sha(work / 'baseline/predictions.csv')
        report.to_csv(work / 'baseline/metrics.csv', index=False)
        try:
            evaluate(work / 'baseline', work); outcome = 'UNEXPECTED-PASS'
        except Refusal as exc:
            outcome = str(exc)
        (work / 'OBSERVED.md').write_text('# Observed check\n\n' + outcome + '\n', encoding='utf-8')
        cases.append({'case': name, 'passed': outcome != 'UNEXPECTED-PASS', 'observed': outcome})
    work = output / 'fit-failure-stub'; run.prepare(work, 1)
    args = SimpleNamespace(workspace=work, candidate='failed-stub', model='median', features='all', metric='MAE')
    with patch.object(run.DummyRegressor, 'fit', side_effect=RuntimeError('deliberate no-training failure')):
        try: run.run(args)
        except RuntimeError: pass
    ledger = pd.read_csv(work / 'ATTEMPTS.csv')
    retained = len(ledger) == 1 and ledger.iloc[0].status == 'failed' and not (work / 'RUNNING.lock').exists()
    try:
        run.run(SimpleNamespace(**{**vars(args), 'candidate': 'retry'})); refused = False
    except Refusal as exc:
        refused = 'budget exhausted' in str(exc)
    cases.append({'case': 'charged-failure-and-refused-retry', 'passed': retained and refused, 'observed': 'one simulated failed attempt; retry refused; zero model fits'})
    pd.DataFrame(cases).to_csv(output / 'CHECKS.csv', index=False)
    print(pd.DataFrame(cases).to_string(index=False))
    if not all(c['passed'] for c in cases): raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--baseline', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); main(args.baseline.resolve(), args.output.resolve())

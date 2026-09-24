"""Recompute a candidate's score from fixed rows and original targets."""
import argparse
import math
from pathlib import Path
import numpy as np
import pandas as pd
from task import Refusal, load_data, split, sha, identity, METRIC


def evaluate(candidate, experiment):
    candidate, experiment = Path(candidate), Path(experiment)
    contract = pd.read_csv(experiment / 'CONTRACT.csv', dtype=str).set_index('key').value.to_dict()
    if contract['package_sha256'] != identity() or contract['metric'] != METRIC:
        raise Refusal('Package or metric contract changed')
    if sha(experiment / 'SPLIT.csv') != contract['split_sha256']:
        raise Refusal('Saved split changed')
    data = load_data()
    expected = split(data).query("partition == 'selection'").row_id.to_numpy()
    prediction = pd.read_csv(candidate / 'predictions.csv')
    if list(prediction.columns) != ['row_id', 'actual', 'prediction']:
        raise Refusal('Prediction schema mismatch')
    if not np.array_equal(prediction.row_id.to_numpy(), expected):
        raise Refusal('Missing, reordered, duplicate, or wrong partition rows')
    if not np.array_equal(prediction.actual.to_numpy(), data.loc[expected, 'quality'].to_numpy()):
        raise Refusal('Targets differ from pinned source')
    if not np.isfinite(prediction.prediction.to_numpy()).all():
        raise Refusal('Non-finite prediction')
    report = pd.read_csv(candidate / 'metrics.csv', dtype=str).iloc[0]
    if report['candidate'] != candidate.name or report['metric'] != METRIC:
        raise Refusal('Candidate identity or metric mismatch')
    if report['predictions_sha256'] != sha(candidate / 'predictions.csv'):
        raise Refusal('Prediction hash mismatch')
    measured = float(np.abs(prediction.actual - prediction.prediction).mean())
    if not math.isclose(float(report['selection_MAE']), measured, rel_tol=1e-10, abs_tol=1e-10):
        raise Refusal('Summary disagrees with predictions')
    requests = pd.read_csv(experiment / 'ATTEMPTS.csv', dtype=str)
    rows = requests[requests.candidate == candidate.name]
    if len(rows) != 1 or rows.iloc[0].status != 'succeeded':
        raise Refusal('Candidate has no unique successful charged attempt')
    if report['model'] != rows.iloc[0].model or report['features'] != rows.iloc[0].features:
        raise Refusal('Recipe differs from charged attempt')
    return measured


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('candidate', type=Path); p.add_argument('--experiment', type=Path, required=True)
    args = p.parse_args()
    try:
        value = evaluate(args.candidate, args.experiment)
        print(f'PASS: checked selection MAE {value:.12f}')
    except (Refusal, OSError, ValueError, KeyError) as exc:
        print('REFUSED: ' + str(exc)); raise SystemExit(2)

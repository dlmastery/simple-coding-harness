"""One separately budgeted screening fit; generated for the course walkthrough."""
import argparse
import hashlib
import importlib.util
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--model', choices=['tree', 'forest'], required=True)
a = p.parse_args()
out = a.output.resolve()
out.mkdir(parents=True, exist_ok=False)  # reserve this attempt; do not overwrite failures
def save(name, body):
    (out / name).write_text(body.rstrip()+'\n', encoding='utf-8', newline='\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

save('BEFORE.md', f'# Screening attempt\n\nModel: {a.model}\nFeatures: all\nSeed: 17\nTrain: 2011-01-01 through 2011-03-31\nSelection: 2012-01-01 through 2012-01-31\nMetric: MAE\nModel fits allocated here: 1\nTool SHA-256: {sha(a.repo / "rsi/tools/lab.py")}\nRunner SHA-256: {sha(Path(__file__))}\nNo final evaluation. Failed attempts remain allocated.')
try:
    spec = importlib.util.spec_from_file_location('scientist_models', a.repo / 'rsi/tools/lab.py')
    lab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab)
    data = lab.read_data('bike')
    train = data.index[(data.dteday >= '2011-01-01') & (data.dteday < '2011-04-01')]
    selection = data.index[(data.dteday >= '2012-01-01') & (data.dteday < '2012-02-01')]
    assert len(train) and len(selection) and set(train).isdisjoint(selection)
    columns = lab.feature_names('bike', 'all', data)
    pd.DataFrame({'row': train}).to_csv(out / 'TRAIN-ROWS.csv', index=False)
    pd.DataFrame({'row': selection}).to_csv(out / 'SELECTION-ROWS.csv', index=False)
    start = time.perf_counter()
    fitted = lab.pipeline('bike', a.model, columns, 17)
    fitted.fit(data.loc[train, columns], data.loc[train, 'cnt'])
    predicted = np.maximum(fitted.predict(data.loc[selection, columns]), 0)
    elapsed = time.perf_counter() - start
    actual = data.loc[selection, 'cnt'].to_numpy()
    score = float(np.mean(np.abs(actual - predicted)))
    pd.DataFrame({'row': selection, 'actual': actual, 'predicted': predicted}).to_csv(out / 'predictions.csv', index=False)
    n_seen = int(fitted.named_steps['prepare'].named_transformers_['numeric'].named_steps['scale'].n_samples_seen_)
    assert n_seen == len(train)
    save('RESULT.md', f'# Screening result\n\nModel: {a.model}\nSelection MAE: {score:.12f}\nFit and prediction seconds: {elapsed:.9f}\nTraining rows: {len(train)}\nSelection rows: {len(selection)}\nScaler training rows seen: {n_seen}\nPython: {platform.python_version()}\nscikit-learn: {sklearn.__version__}\npandas: {pd.__version__}\nNumPy: {np.__version__}\n\nOnly the recorded subset fits preprocessing and estimator parameters. Source bytes are public; this is not a secret evaluation service.')
    print((out / 'RESULT.md').read_text())
except Exception as exc:
    save('FAILURE.md', f'# Retained failed attempt\n\n{type(exc).__name__}: {exc}\nThis attempt is not refunded.')
    raise

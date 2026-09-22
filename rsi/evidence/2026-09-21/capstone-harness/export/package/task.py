"""Fixed scientific contract for a generated student-owned harness."""
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_HASH = '76c3f809815c17c07212622f776311faeb31e87610d52c26d87d6e361b169836'
FEATURES = ['fixed acidity', 'volatile acidity', 'citric acid', 'residual sugar',
            'chlorides', 'free sulfur dioxide', 'total sulfur dioxide',
            'density', 'pH', 'sulphates', 'alcohol']
TARGET = 'quality'
METRIC = 'MAE'


class Refusal(ValueError):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_data():
    source = ROOT / 'data/winequality-white.csv'
    if sha(source) != DATA_HASH:
        raise Refusal('Source data hash changed')
    data = pd.read_csv(source, sep=';')
    if list(data.columns) != FEATURES + [TARGET] or not np.isfinite(data.to_numpy()).all():
        raise Refusal('Unexpected schema or non-finite data')
    data.index.name = 'row_id'
    return data


def split(data):
    # Targets never participate in group identity. Equal inputs cannot cross folds.
    keys = data[FEATURES].apply(lambda row: '|'.join(format(float(v), '.17g') for v in row), axis=1)
    groups = keys.map(lambda key: hashlib.sha256(('white-quality-v1|' + key).encode()).hexdigest())
    buckets = groups.map(lambda h: int(h[:12], 16) % 10000)
    partitions = np.where(buckets < 6000, 'train', np.where(buckets < 8000, 'selection', 'evaluation'))
    result = pd.DataFrame({'row_id': data.index, 'group': groups, 'partition': partitions})
    if set(result.partition) != {'train', 'selection', 'evaluation'}:
        raise Refusal('Empty partition')
    if result.groupby('group').partition.nunique().max() != 1:
        raise Refusal('Input groups cross partitions')
    return result


def validate_features(text):
    chosen = FEATURES if text == 'all' else [s.strip() for s in text.split(',')]
    if not chosen or len(set(chosen)) != len(chosen) or not set(chosen) <= set(FEATURES):
        raise Refusal('Features must be unique permitted inputs; target quality is forbidden')
    return chosen


def identity():
    names = ['task.py', 'run.py', 'evaluate.py', 'TASK.md', 'requirements.txt']
    return hashlib.sha256('\n'.join(n + ':' + sha(ROOT / n) for n in names).encode()).hexdigest()

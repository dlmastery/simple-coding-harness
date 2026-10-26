"""One admitted fit using a copied public-data directory and frozen builder."""
import argparse
import importlib.util
from pathlib import Path
import time

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error
from threadpoolctl import threadpool_limits


def run(task, engine, candidate, kind, output):
    schema = pd.read_csv(task / "SCHEMA.csv", keep_default_na=False)
    target, = schema[schema.role == "target"].column.tolist()
    features = schema[schema.role == "feature"].column.tolist()
    dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
    train = pd.read_csv(task / "train.csv", dtype=dtype)
    selection = pd.read_csv(task / "selection.csv", dtype=dtype)
    spec = importlib.util.spec_from_file_location("frozen_engine", engine)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.build(schema, kind, candidate, seed=41)
    scale = float(np.mean(np.abs(train[target] - np.median(train[target])))) if kind == "regression" else 1.
    if scale <= 0:
        raise ValueError("Training normalization scale is zero")
    started = time.perf_counter()
    records = []
    with threadpool_limits(limits=1):
        model.fit(train[features], train[target])
        fit_seconds = time.perf_counter() - started
        for name, data in (("train", train), ("selection", selection)):
            prediction = model.predict(data[features])
            score = balanced_accuracy_score(data[target], prediction) if kind == "classification" else mean_absolute_error(data[target], prediction)
            loss = 1 - score if kind == "classification" else score / scale
            pd.DataFrame(dict(row_id=data.row_id, truth=data[target], prediction=prediction)).to_csv(output / f"{name}-predictions.csv", index=False)
            records.append(dict(split=name, metric="balanced_accuracy" if kind == "classification" else "MAE",
                                score=score, loss=loss, training_scale=scale, fit_seconds=fit_seconds))
    pd.DataFrame(records).to_csv(output / "METRICS.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("task", "engine", "candidate", "kind", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    run(Path(args.task), Path(args.engine), args.candidate, args.kind, Path(args.output))

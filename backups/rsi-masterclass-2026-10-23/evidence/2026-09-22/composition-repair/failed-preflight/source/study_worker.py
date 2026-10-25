"""One subprocess, one model fit, declared public inputs and optional final scoring."""
import argparse
import importlib.util
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error
from threadpoolctl import threadpool_limits


def run(args):
    if (args.phase == "search") != (args.final_file is None):
        raise ValueError("Final rows are permitted only in the scoring phase")
    task, builder, output = Path(args.task), Path(args.builder), Path(args.output)
    schema = pd.read_csv(task / "SCHEMA.csv", keep_default_na=False)
    target, = schema[schema.role == "target"].column.tolist()
    features = schema[schema.role == "feature"].column.tolist()
    dtype = {r.column: str if r.kind == "categorical" else float for r in schema.itertuples()}
    train = pd.read_csv(task / "train.csv", dtype=dtype)
    frames = {"train": train, "selection": pd.read_csv(task / "selection.csv", dtype=dtype)}
    if args.phase == "score":
        frames["final"] = pd.read_csv(args.final_file, dtype=dtype)
    sys.path.insert(0, str(builder.parent))
    spec = importlib.util.spec_from_file_location("candidate", builder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.build(schema, args.kind, seed=41)
    scale = float(np.mean(np.abs(train[target]-np.median(train[target])))) if args.kind == "regression" else 1.
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Invalid training normalization scale")
    rows = []
    with threadpool_limits(limits=1):
        start = time.perf_counter()
        model.fit(train[features], train[target])
        fit_seconds = time.perf_counter()-start
        for split, frame in frames.items():
            predictions = model.predict(frame[features])
            score = float(balanced_accuracy_score(frame[target], predictions) if args.kind == "classification" else mean_absolute_error(frame[target], predictions))
            loss = 1-score if args.kind == "classification" else score/scale
            pd.DataFrame(dict(row_id=frame.row_id, truth=frame[target], prediction=predictions)).to_csv(output / f"{split}-predictions.csv", index=False)
            rows.append(dict(split=split, score=score, loss=loss, training_scale=scale, fit_seconds=fit_seconds))
    pd.DataFrame(rows).to_csv(output / "METRICS.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["search", "score"], required=True)
    for name in ("task", "builder", "kind", "output"):
        parser.add_argument("--"+name, required=True)
    parser.add_argument("--final-file")
    run(parser.parse_args())

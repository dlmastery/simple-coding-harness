"""Development-only noise diagnostic using privileged generator knowledge; zero fits."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def diagnose(work, out):
    if out.exists():
        raise ValueError("Preserve earlier diagnostics")
    if not pd.read_csv(work / "EVALUATION-CHECKS.csv").passed.all():
        raise ValueError("Audit development first")
    out.mkdir(parents=True)
    results = pd.read_csv(work / "RESULTS.csv")
    rows = []
    for seed in sorted(results.seed.unique()):
        data = np.load(work / "data" / f"task-{seed}.npz", allow_pickle=False)
        rng = np.random.default_rng(seed)
        raw = rng.normal(size=(2000, 10))
        coefficients = rng.uniform(.6, 1.4, 4) * rng.choice([-1., 1.], 4)
        family = (seed - 1101) % 3
        if family == 0:
            signal = coefficients[0] * raw[:, 0] * raw[:, 1] + coefficients[1] * raw[:, 2] + coefficients[2] * raw[:, 3] + .4 * coefficients[3] * raw[:, 4] * raw[:, 5]
        elif family == 1:
            signal = raw[:, :4] @ coefficients
        else:
            signal = coefficients[0] * (raw[:, 0] ** 2 - 1) + coefficients[1] * raw[:, 1] + coefficients[2] * np.sin(raw[:, 2]) + coefficients[3] * raw[:, 3] * raw[:, 4]
        noise = rng.normal(scale=.3, size=2000)
        kind = str(data["kind"])
        generated = signal + noise if kind == "regression" else (signal + noise > .25).astype(int)
        if not np.array_equal(data["y_selection"], generated[1200:]):
            raise ValueError("Diagnostic generator did not reconstruct actual targets")
        actual = data["y_selection"]
        privileged = signal[1200:] if kind == "regression" else (signal[1200:] > .25).astype(int)
        if kind == "regression":
            score = np.abs(actual - privileged).mean()
            loss = score / np.abs(actual - np.median(data["y_train"])).mean()
        else:
            score = np.mean([(privileged[actual == label] == label).mean() for label in np.unique(actual)])
            loss = 2 * (1 - score)
        pair = results[results.seed == seed].set_index("arm")
        rows.append(dict(seed=seed, kind=kind, family=family, parent_score=pair.loc["parent", "score"],
                         child_score=pair.loc["child", "score"], privileged_signal_score=score,
                         parent_loss=pair.loc["parent", "loss"], child_loss=pair.loc["child", "loss"],
                         privileged_signal_loss=loss, parent_minus_signal_loss=pair.loc["parent", "loss"] - loss))
        pd.DataFrame(dict(row_id=data["selection_ids"], actual=actual, privileged_signal_prediction=privileged,
                          latent_signal=signal[1200:], latent_noise=noise[1200:])).to_csv(out / f"task-{seed}.csv", index=False)
    table = pd.DataFrame(rows)
    table.to_csv(out / "DIAGNOSTIC.csv", index=False)
    report = ("# Why the current tasks have little predictive headroom\n\n"
        "This is a retrospective, privileged development diagnostic. It reconstructs the known "
        "generator's clean signal and noise for the six existing development tasks. No new task "
        "or model fit is created, and no final data is read. These signal values were not supplied "
        "to candidate builders.\n\n"
        f"For regression, the expected absolute Gaussian noise is 0.3 sqrt(2/pi) = {0.3 * np.sqrt(2 / np.pi):.9f}. "
        "This is the population MAE of the known conditional median. Its realized error on a finite "
        "selection sample fluctuates; it is not a hard sample-level lower bound.\n\n"
        "For classification, the diagnostic thresholds the noiseless signal at 0.25. It is a "
        "privileged reference, not an exact Bayes optimum for balanced accuracy. Class weighting "
        "and sampling affect that metric. Do not report it as an attainable learned baseline.\n\n"
        f"Mean parent-minus-privileged-reference normalized selection loss: {table.parent_minus_signal_loss.mean():.9f}.\n\n"
        "The parent already represents the linear and pairwise parts of the grammar. The child "
        "mainly addresses the remaining smooth term. Read each raw score in DIAGNOSTIC.csv. "
        "A small average change is therefore compatible with a useful local feature correction. "
        "It does not justify lowering the already used gate, selecting only a favorable task, "
        "or calling this final evidence.\n\n"
        "The next benchmark design needs documented functional diversity and sound controls, "
        "while keeping these failures and earlier exposed tasks as development evidence. "
        "Do not turn a stream of new seeds from this narrow grammar into a claim of broad RSI.\n")
    (out / "README.md").write_text(report, encoding="utf-8")
    (out / "SOURCE.md").write_text(
        f"Diagnostic source SHA256: {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}\n"
        f"Input RESULTS.csv SHA256: {hashlib.sha256((work / 'RESULTS.csv').read_bytes()).hexdigest()}\n"
        "All six reconstructed selection targets match their saved arrays exactly.\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    diagnose(args.workspace.resolve(), args.destination.resolve())

"""Small tabular tasks from the OpenML AutoML Benchmark: where they live, and how a submission is graded.

The course uses eight OpenML datasets that the AutoML Benchmark (AMLB, Gijsbers
et al., JMLR 2024) also uses. `prepare` downloads each one once (no account
needed) and splits it 80/20 into

    <data>/<id>/public/    what the agent sees: description.md, train.csv, test.csv, sample_submission.csv
    <data>/<id>/private/   answers.csv and reference.json: only the grader reads these

Metrics follow AMLB: AUC for binary tasks, log loss for multiclass, RMSE for
regression. Scores are normalized the AMLB way, so tasks with different
metrics can be averaged:

    norm = (score - constant predictor) / (random forest - constant predictor)

0 means "no better than predicting the prior", 1 means "as good as a plain
random forest", above 1 means better than the forest.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(os.environ.get("AMLB_DATA", Path.home() / "rsi-data" / "amlb"))

# id -> (OpenML data id, kind, short description of the target)
TASKS = {
    "adult":          (1590, "binary", "whether a person's income exceeds $50K a year, from census records"),
    "amazon":         (4135, "binary", "whether an employee's access request to a resource is approved"),
    "house-sales":    (42092, "regression", "the sale price of a house in King County, USA"),
    "bank-marketing": (1461, "binary", "whether a client subscribes to a term deposit after a phone campaign"),
    "churn":          (40701, "binary", "whether a telecom customer leaves the company"),
    "diamonds":       (42225, "regression", "the price of a diamond from its cut, color, clarity and size"),
    "jungle-chess":   (41027, "multiclass", "the outcome of a two-piece endgame of the board game Jungle"),
    "cnae-9":         (1468, "multiclass", "the business category of a company from word counts of its description"),
}

SPLITS = {
    # evolve: the only tasks an improver may look at while it edits the harness
    "evolve": ["adult", "amazon", "house-sales"],
    # heldout: same kinds of problem (binary with categoricals, price regression), new datasets
    "heldout": ["bank-marketing", "churn", "diamonds"],
    # ood: a kind the improver never saw (multiclass log loss; one is 856 sparse word-count columns)
    "ood": ["jungle-chess", "cnae-9"],
}
ALL = [c for split in SPLITS.values() for c in split]

METRIC = {"binary": ("AUC", False), "multiclass": ("log loss", True), "regression": ("RMSE", True)}


@dataclass
class Competition:
    id: str
    public: Path
    lower_is_better: bool
    description: str


def _describe(cid, name, kind, what, target, classes):
    metric, lower = METRIC[kind]
    if kind == "binary":
        sub = f"`id` and `{target}`: the predicted probability that `{target}` is `{classes[1]}`"
    elif kind == "multiclass":
        sub = "`id` and one column per class (" + ", ".join(f"`{c}`" for c in classes) + \
              ") holding predicted probabilities that sum to 1"
    else:
        sub = f"`id` and `{target}`: the predicted value"
    return (f"# {name}\n\nPredict {what}.\n\n"
            f"The target column is `{target}`. `train.csv` has the target; `test.csv` does not.\n\n"
            f"Metric: {metric} on the test set ({'lower' if lower else 'higher'} is better).\n\n"
            f"Submission: a CSV with columns {sub}, one row per test `id`, "
            f"in the format of `sample_submission.csv`.\n")


def prepare(cid, seed=0):
    """Download one task from OpenML and write its public and private files."""
    from sklearn.datasets import fetch_openml
    from sklearn.model_selection import train_test_split
    did, kind, what = TASKS[cid]
    root = DATA / cid
    if (root / "private" / "reference.json").exists():
        return root
    b = fetch_openml(data_id=did, as_frame=True, parser="auto", data_home=str(DATA / "_openml"))
    target = b.target.name or "target"
    X = b.data.copy()
    y = b.target.astype(str) if kind != "regression" else b.target.astype(float)
    classes = sorted(y.unique()) if kind != "regression" else []
    if kind == "binary":   # the minority class is the positive class
        classes = sorted(classes, key=lambda c: -(y == c).sum())
    df = X.assign(**{target: y})
    df.insert(0, "id", np.arange(len(df)))
    strat = y if kind != "regression" else None
    tr, te = train_test_split(df, test_size=0.2, random_state=seed, stratify=strat)
    (root / "public").mkdir(parents=True, exist_ok=True)
    (root / "private").mkdir(parents=True, exist_ok=True)
    tr.to_csv(root / "public" / "train.csv", index=False)
    te.drop(columns=[target]).to_csv(root / "public" / "test.csv", index=False)
    te[["id", target]].to_csv(root / "private" / "answers.csv", index=False)
    if kind == "multiclass":
        sample = pd.DataFrame({"id": te["id"], **{c: 1 / len(classes) for c in classes}})
    elif kind == "binary":
        sample = pd.DataFrame({"id": te["id"], target: 0.5})
    else:
        sample = pd.DataFrame({"id": te["id"], target: float(tr[target].mean())})
    sample.to_csv(root / "public" / "sample_submission.csv", index=False)
    (root / "public" / "description.md").write_text(
        _describe(cid, b.details["name"], kind, what, target, classes), encoding="utf-8")
    meta = {"kind": kind, "target": target, "classes": classes, "name": b.details["name"], "openml_id": did}
    (root / "private" / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    ref = {"constant": _score(meta, te, _constant(meta, tr, te)), "random_forest": _score(meta, te, _forest(meta, tr, te))}
    (root / "private" / "reference.json").write_text(json.dumps(ref, indent=1), encoding="utf-8")
    return root


def _constant(meta, tr, te):
    t = meta["target"]
    if meta["kind"] == "regression":
        return pd.DataFrame({"id": te["id"], t: tr[t].mean()})
    prior = tr[t].value_counts(normalize=True)
    if meta["kind"] == "binary":
        return pd.DataFrame({"id": te["id"], t: prior.get(meta["classes"][1], 0.0)})
    return pd.DataFrame({"id": te["id"], **{c: prior.get(c, 0.0) for c in meta["classes"]}})


def _forest(meta, tr, te):
    """The AMLB reference point: a random forest with plain ordinal encoding and median imputation."""
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    t = meta["target"]
    feats = [c for c in tr.columns if c not in ("id", t)]
    both = pd.concat([tr[feats], te[feats]])
    for c in feats:
        if not pd.api.types.is_numeric_dtype(both[c]):
            both[c] = both[c].astype("category").cat.codes
    both = both.fillna(both.median(numeric_only=True))
    Xtr, Xte = both.iloc[:len(tr)], both.iloc[len(tr):]
    if meta["kind"] == "regression":
        m = RandomForestRegressor(300, n_jobs=-1, random_state=0).fit(Xtr, tr[t])
        return pd.DataFrame({"id": te["id"], t: m.predict(Xte)})
    m = RandomForestClassifier(300, n_jobs=-1, random_state=0).fit(Xtr, tr[t])
    p = pd.DataFrame(m.predict_proba(Xte), columns=m.classes_)
    if meta["kind"] == "binary":
        return pd.DataFrame({"id": te["id"].values, t: p[meta["classes"][1]].values})
    return pd.DataFrame({"id": te["id"].values, **{c: p[c].values for c in meta["classes"]}})


def _score(meta, answers, sub):
    """The task's metric; raises ValueError for a malformed submission."""
    from sklearn.metrics import log_loss, mean_squared_error, roc_auc_score
    t = meta["target"]
    sub = sub.copy()
    if "id" not in sub.columns or len(sub) != len(answers) or set(sub["id"]) != set(answers["id"]):
        raise ValueError("submission ids do not match the test ids")
    merged = answers[["id", t]].rename(columns={t: "__true"}).merge(sub, on="id")
    if meta["kind"] == "binary":
        p = pd.to_numeric(merged[t], errors="raise").astype(float)
        if p.isna().any():
            raise ValueError("missing predictions")
        return float(roc_auc_score(merged["__true"].astype(str) == meta["classes"][1], p))
    if meta["kind"] == "regression":
        p = pd.to_numeric(merged[t], errors="raise").astype(float)
        if p.isna().any() or not np.isfinite(p).all():
            raise ValueError("missing or infinite predictions")
        return float(np.sqrt(mean_squared_error(merged["__true"].astype(float), p)))
    cols = [str(c) for c in meta["classes"]]
    merged.columns = [str(c) for c in merged.columns]
    missing = [c for c in cols if c not in merged.columns]
    if missing:
        raise ValueError(f"missing class columns {missing}")
    P = merged[cols].apply(pd.to_numeric, errors="raise").to_numpy(float)
    if np.isnan(P).any():
        raise ValueError("missing predictions")
    P = np.clip(P, 1e-15, None)
    P = P / P.sum(axis=1, keepdims=True)
    return float(log_loss(merged["__true"].astype(str), P, labels=cols))


def get(cid):
    root = DATA / cid
    meta = json.loads((root / "private" / "meta.json").read_text(encoding="utf-8"))
    return Competition(cid, root / "public", METRIC[meta["kind"]][1],
                       (root / "public" / "description.md").read_text(encoding="utf-8"))


def grade(cid, submission_csv):
    """Score one submission, then normalize it between the constant predictor (0) and the random forest (1)."""
    root = DATA / cid
    meta = json.loads((root / "private" / "meta.json").read_text(encoding="utf-8"))
    ref = json.loads((root / "private" / "reference.json").read_text(encoding="utf-8"))
    answers = pd.read_csv(root / "private" / "answers.csv")
    out = {"score": None, "valid": False, "norm": 0.0, "beats_forest": False}
    try:
        score = _score(meta, answers, pd.read_csv(submission_csv))
    except Exception:  # noqa: BLE001 - any malformed submission scores 0
        return out
    norm = (score - ref["constant"]) / (ref["random_forest"] - ref["constant"])
    out.update(score=score, valid=True, norm=float(max(norm, 0.0)), beats_forest=bool(norm > 1.0))
    return out


def obfuscated_description(cid):
    """The same task with the dataset's name removed: lab 05's counterfactual (the CHASE idea, arXiv 2609.18366)."""
    d = get(cid).description
    name = json.loads((DATA / cid / "private" / "meta.json").read_text(encoding="utf-8"))["name"]
    return d.replace(f"# {name}", "# A tabular prediction task").replace(name, "the dataset")

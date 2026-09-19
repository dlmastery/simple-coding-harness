"""The recipe space every pack shares, and the one fit function.

A recipe is one dict with five fields: `model` (logreg, rf, hgb), `hyper`
(the one hyper-parameter of that model: C, max_depth or learning_rate),
`scale`, `encode` and `class_weight`. 3 models x 3 hyper values x 2 x 2 x 2 =
72 recipes; the static list a regular harness walks is the 24 at the middle
hyper value. The space is fixed so that a card learned on one problem can
apply to the next: experience transfers only across a shared vocabulary.
"""

import json
import warnings

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

TARGET = "target"

HYPER = {                                   # the one hyper-parameter per model, middle value = default
    "logreg": ("C", [0.25, 1, 4]),
    "rf": ("max_depth", [8, 16, None]),
    "hgb": ("learning_rate", [0.05, 0.1, 0.3]),
}

SCHEMA = {
    "model": ["logreg", "rf", "hgb"],
    "hyper": {name: values for name, (_, values) in HYPER.items()},
    "scale": ["yes", "no"],
    "encode": ["onehot", "ordinal"],
    "class_weight": ["none", "balanced"],
}
FIELDS = ("model", "hyper", "scale", "encode", "class_weight")

BASELINE = {"model": "logreg", "hyper": 1, "scale": "yes", "encode": "onehot", "class_weight": "none"}

# small ensembles keep a fit under a second on the bundled tables; the search is the point, not the model
N_TREES = 60
N_ROUNDS = 60


def key(recipe):
    """The recipe as one canonical string: the identity a trace, a cache or a visited-set uses."""
    return json.dumps(recipe, sort_keys=True)


def validate(recipe):
    """A recipe has exactly the five fields, each with a value from the schema. Anything else is not a recipe."""
    if not isinstance(recipe, dict) or set(recipe) != set(FIELDS):
        raise ValueError(f"a recipe has exactly the fields {list(FIELDS)}")
    for field in ("model", "scale", "encode", "class_weight"):
        if recipe[field] not in SCHEMA[field]:
            raise ValueError(f"{field}={recipe[field]!r} is not one of {SCHEMA[field]}")
    if recipe["hyper"] not in SCHEMA["hyper"][recipe["model"]]:
        raise ValueError(f"hyper={recipe['hyper']!r} is not one of {SCHEMA['hyper'][recipe['model']]} for {recipe['model']}")
    return recipe


def grid():
    """All 72 recipes in one fixed order: model, hyper, scale, encode, class_weight."""
    out = []
    for model in SCHEMA["model"]:
        for hyper in SCHEMA["hyper"][model]:
            for scale in SCHEMA["scale"]:
                for encode in SCHEMA["encode"]:
                    for cw in SCHEMA["class_weight"]:
                        out.append({"model": model, "hyper": hyper, "scale": scale, "encode": encode, "class_weight": cw})
    return out


def static_list():
    """The 24 recipes at the middle hyper value, in grid order: what a regular harness walks every Monday."""
    return [r for r in grid() if r["hyper"] == SCHEMA["hyper"][r["model"]][1]]


def neighbours(recipe):
    """The recipes one field away from this one, in field order: the local moves a search policy makes."""
    out = []
    for field in FIELDS:
        values = SCHEMA["hyper"][recipe["model"]] if field == "hyper" else SCHEMA[field]
        for value in values:
            if value != recipe[field]:
                other = dict(recipe, **{field: value})
                if field == "model":   # a new model needs its own middle hyper value
                    other["hyper"] = SCHEMA["hyper"][value][1]
                out.append(other)
    return out


def build(recipe, df):
    categorical = [c for c in df.columns if c != TARGET and df[c].dtype == object]
    numeric = [c for c in df.columns if c != TARGET and c not in categorical]
    scaler = StandardScaler() if recipe["scale"] == "yes" else "passthrough"
    encoder = {
        "onehot": OneHotEncoder(handle_unknown="ignore"),
        "ordinal": OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
    }[recipe["encode"]]
    columns = ColumnTransformer([("num", scaler, numeric), ("cat", encoder, categorical)], sparse_threshold=0)
    cw = None if recipe["class_weight"] == "none" else "balanced"
    model = {
        "logreg": lambda: LogisticRegression(C=recipe["hyper"], max_iter=2000, class_weight=cw),
        "rf": lambda: RandomForestClassifier(n_estimators=N_TREES, max_depth=recipe["hyper"], random_state=0, class_weight=cw),
        "hgb": lambda: HistGradientBoostingClassifier(learning_rate=recipe["hyper"], max_iter=N_ROUNDS, random_state=0, class_weight=cw),
    }[recipe["model"]]()
    return Pipeline([("columns", columns), ("model", model)])


def score(pipe, df, metric):
    """ROC-AUC on one split: the positive-class probability for binary, macro one-vs-rest for multiclass."""
    proba = pipe.predict_proba(df.drop(columns=TARGET))
    if metric == "roc_auc":
        return float(roc_auc_score(df[TARGET], proba[:, 1]))
    if metric == "roc_auc_ovr_macro":
        return float(roc_auc_score(df[TARGET], proba, multi_class="ovr", average="macro"))
    raise ValueError(f"unknown metric {metric!r}")


def fit(recipe, train, val, metric="roc_auc"):
    """One fit, one validation score. Never raises: a recipe that cannot fit is a result too (val_score None, error set)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe = build(recipe, train)
            pipe.fit(train.drop(columns=TARGET), train[TARGET])
            return {"val_score": round(score(pipe, val, metric), 4), "error": None, "pipeline": pipe}
    except Exception as e:
        return {"val_score": None, "error": f"{type(e).__name__}: {e}"[:120], "pipeline": None}

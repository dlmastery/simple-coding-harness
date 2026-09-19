"""Step 01 - a recipe is one dict with five fields, each from a short list; a fit
is one function that never raises.

The schema is the whole search space: 2 x 3 x 3 x 3 x 2 = 108 recipes. `encode:
none` passes strings straight into the model, which every sklearn model refuses
when the table has categoricals: those are the wasted fits the memory learns to
avoid. `capacity` is the one hyper-parameter, and it means something different
per model (C for the linear model, trees or boosting rounds for the others).
"""

import warnings

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from common.data import TARGET, categorical_columns

SCHEMA = {
    "scale": ["standard", "none"],
    "encode": ["onehot", "ordinal", "none"],
    "model": ["lr", "rf", "hgb"],
    "capacity": ["low", "mid", "high"],
    "class_weight": ["none", "balanced"],
}

BASELINE = {"scale": "standard", "encode": "onehot", "model": "lr", "capacity": "mid", "class_weight": "none"}

CAPACITY = {
    "lr": {"low": 0.1, "mid": 1.0, "high": 10.0},   # C
    "rf": {"low": 20, "mid": 50, "high": 100},      # trees
    "hgb": {"low": 20, "mid": 50, "high": 100},     # boosting rounds
}

MODELS = {
    "lr": lambda size, cw: LogisticRegression(C=size, max_iter=1000, class_weight=cw),
    "rf": lambda size, cw: RandomForestClassifier(n_estimators=size, random_state=0, class_weight=cw),
    "hgb": lambda size, cw: HistGradientBoostingClassifier(max_iter=size, random_state=0, class_weight=cw),
}


def validate(recipe, schema=SCHEMA):
    """A recipe has exactly the schema's fields, each with one of its values. Anything else is not a recipe."""
    if not isinstance(recipe, dict) or set(recipe) != set(schema):
        raise ValueError(f"a recipe has exactly the fields {sorted(schema)}")
    for field, value in recipe.items():
        if value not in schema[field]:
            raise ValueError(f"{field}={value!r} is not one of {schema[field]}")
    return recipe


def build(recipe, df):
    numeric = [c for c in df.columns if c != TARGET and c not in categorical_columns(df)]
    categorical = categorical_columns(df)
    scaler = StandardScaler() if recipe["scale"] == "standard" else "passthrough"
    encoder = {
        "onehot": OneHotEncoder(handle_unknown="ignore"),
        "ordinal": OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
        "none": "passthrough",   # strings reach the model: a ValueError, and a wasted fit
    }[recipe["encode"]]
    columns = ColumnTransformer([("num", scaler, numeric), ("cat", encoder, categorical)], sparse_threshold=0)
    weight = None if recipe["class_weight"] == "none" else "balanced"
    model = MODELS[recipe["model"]](CAPACITY[recipe["model"]][recipe["capacity"]], weight)
    return Pipeline([("columns", columns), ("model", model)])


def fit_recipe(recipe, train, val):
    """One fit, one validation AUC. Never raises: a recipe that cannot fit is a result too."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe = build(recipe, train)
            pipe.fit(train.drop(columns=TARGET), train[TARGET])
            auc = roc_auc_score(val[TARGET], pipe.predict_proba(val.drop(columns=TARGET))[:, 1])
        return {"val_auc": round(float(auc), 4), "error": None}
    except Exception as e:
        return {"val_auc": None, "error": f"{type(e).__name__}: {e}"[:120]}

"""Conventional mixed-table portfolio, before any agent-authored improvement."""
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import (ExtraTreesClassifier, ExtraTreesRegressor,
                              HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR

CANDIDATES = ["linear", "extra-trees", "hist-boost", "random-forest",
              "rbf-1", "rbf-10", "neighbors-5", "neighbors-25"]


def build(schema, kind, candidate, seed=41):
    if candidate not in CANDIDATES:
        raise ValueError(candidate)
    numeric = schema[(schema.role == "feature") & (schema.kind == "numeric")].column.tolist()
    categorical = schema[(schema.role == "feature") & (schema.kind == "categorical")].column.tolist()
    transforms = []
    if numeric:
        transforms.append(("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        transforms.append(("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical))
    classification = kind == "classification"
    if candidate == "linear":
        model = LogisticRegression(C=1, class_weight="balanced", max_iter=2000, random_state=seed) if classification else Ridge(alpha=1)
    elif candidate == "extra-trees":
        cls = ExtraTreesClassifier if classification else ExtraTreesRegressor
        model = cls(n_estimators=128, min_samples_leaf=1, n_jobs=1, random_state=seed,
                    **({"class_weight": "balanced"} if classification else {}))
    elif candidate == "hist-boost":
        cls = HistGradientBoostingClassifier if classification else HistGradientBoostingRegressor
        model = cls(max_iter=200, learning_rate=.1, max_leaf_nodes=31,
                    early_stopping=False, random_state=seed,
                    **({"class_weight": "balanced"} if classification else {}))
    elif candidate == "random-forest":
        cls = RandomForestClassifier if classification else RandomForestRegressor
        model = cls(n_estimators=128, min_samples_leaf=1, n_jobs=1, random_state=seed,
                    **({"class_weight": "balanced"} if classification else {}))
    elif candidate.startswith("rbf-"):
        strength = float(candidate.split("-")[-1])
        model = SVC(C=strength, class_weight="balanced", random_state=seed) if classification else SVR(C=strength, epsilon=.1)
    else:
        neighbors = int(candidate.split("-")[-1])
        cls = KNeighborsClassifier if classification else KNeighborsRegressor
        model = cls(n_neighbors=neighbors, weights="distance", n_jobs=1)
    pipeline = Pipeline([("prepare", ColumnTransformer(transforms, remainder="drop")), ("model", model)])
    return pipeline if classification else TransformedTargetRegressor(regressor=pipeline, transformer=StandardScaler())

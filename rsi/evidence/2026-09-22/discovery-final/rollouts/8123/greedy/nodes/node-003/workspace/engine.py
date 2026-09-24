"""Bounded numerical pipeline builder used by generated candidate programs."""
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.svm import SVC, SVR


def build(kind, family, transform, strength, seed):
    if kind not in ("classification", "regression") or not .01 <= strength <= 100:
        raise ValueError("Unsupported task or out-of-budget model parameter")
    if transform not in ("raw", "pairwise", "quadratic"):
        raise ValueError("Unknown feature operator")
    classifier = kind == "classification"
    if family == "linear":
        model = (LogisticRegression(C=1 / strength, max_iter=1200, class_weight="balanced")
                 if classifier else Ridge(alpha=strength))
    elif family == "boost":
        cls = HistGradientBoostingClassifier if classifier else HistGradientBoostingRegressor
        model = cls(max_iter=100, max_leaf_nodes=max(7, min(63, int(15 * strength))),
                    early_stopping=False, random_state=seed,
                    **({"class_weight": "balanced"} if classifier else {}))
    elif family == "extra":
        cls = ExtraTreesClassifier if classifier else ExtraTreesRegressor
        model = cls(n_estimators=64, min_samples_leaf=max(1, min(20, int(strength))),
                    max_features=1., n_jobs=1, random_state=seed,
                    **({"class_weight": "balanced"} if classifier else {}))
    elif family == "kernel":
        model = SVC(C=strength, class_weight="balanced") if classifier else SVR(C=strength)
    else:
        raise ValueError("Unknown family")
    steps = [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    if transform != "raw":
        steps.extend([("features", PolynomialFeatures(degree=2, interaction_only=transform == "pairwise",
                                                      include_bias=False)),
                      ("feature_scale", StandardScaler())])
    steps.append(("model", model))
    return Pipeline(steps)

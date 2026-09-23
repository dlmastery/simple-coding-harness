"""Second agent-authored revision; explicitly inherits both earlier builders."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import (FunctionTransformer, OrdinalEncoder,
                                   PolynomialFeatures, SplineTransformer, StandardScaler)

from parent_engine import build as parent_build
from revision_one_engine import build as revision_one_build


class NonnegativeLog(BaseEstimator, TransformerMixin):
    def fit(self, values, y=None):
        if np.any(np.asarray(values) < 0):
            raise ValueError("Log-target proposal requires nonnegative training targets")
        return self

    def transform(self, values):
        if np.any(np.asarray(values) < 0):
            raise ValueError("Negative value in log-target transform")
        return np.log1p(values)

    def inverse_transform(self, values):
        return np.expm1(values)


def build(schema, kind, candidate, seed=41):
    if kind == "classification":
        if candidate in {"unscaled-c1", "unscaled-c100"}:
            model = revision_one_build(schema, kind, "rbf-unscaled", seed)
            model.set_params(model__C=1 if candidate == "unscaled-c1" else 100)
            return model
        if candidate == "forest-all-features":
            model = parent_build(schema, kind, "random-forest", seed)
            model.set_params(model__max_features=1., model__min_samples_leaf=2)
            return model
        if candidate == "native-category-boost":
            numeric = schema[(schema.role == "feature") & (schema.kind == "numeric")].column.tolist()
            categorical = schema[(schema.role == "feature") & (schema.kind == "categorical")].column.tolist()
            transforms = []
            if numeric:
                transforms.append(("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
            if categorical:
                transforms.append(("categorical", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan, encoded_missing_value=np.nan), categorical))
            return Pipeline([
                ("prepare", ColumnTransformer(transforms)),
                ("model", HistGradientBoostingClassifier(categorical_features=[False]*len(numeric)+[True]*len(categorical),
                    max_iter=200, max_leaf_nodes=15, learning_rate=.1, l2_regularization=1.,
                    class_weight="balanced", early_stopping=False, random_state=seed))])
    elif kind == "regression":
        if candidate in {"log-boost", "log-svr"}:
            model = parent_build(schema, kind, "hist-boost", seed) if candidate == "log-boost" else revision_one_build(schema, kind, "svr-tight", seed)
            model.set_params(transformer=Pipeline([("log", NonnegativeLog()), ("scale", StandardScaler())]))
            return model
        if candidate == "extra-leaf5":
            model = parent_build(schema, kind, "extra-trees", seed)
            model.regressor.set_params(model__min_samples_leaf=5)
            return model
        if candidate == "quadratic-splines":
            model = parent_build(schema, kind, "linear", seed)
            prepare = model.regressor.named_steps["prepare"]
            model.set_params(regressor=Pipeline([
                ("prepare", prepare),
                ("basis", FeatureUnion([
                    ("quadratic", PolynomialFeatures(degree=2, include_bias=False)),
                    ("smooth", SplineTransformer(n_knots=5, degree=3, include_bias=False, extrapolation="linear"))])),
                ("scale", StandardScaler()), ("model", Ridge(alpha=10))]))
            return model
    raise ValueError((kind, candidate))

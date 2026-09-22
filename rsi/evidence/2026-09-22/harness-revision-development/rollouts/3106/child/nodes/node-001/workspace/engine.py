"""Agent-proposed child builder; original models remain in parent_engine.py."""
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer, StandardScaler

from parent_engine import build as parent_build


def build(kind, family, transform, strength, seed):
    if transform != "quadratic-splines":
        return parent_build(kind, family, transform, strength, seed)
    if family != "linear":
        raise ValueError("The new basis is a linear-model proposal only")
    base = parent_build(kind, family, "raw", strength, seed)
    steps = list(base.steps)
    basis = FeatureUnion([
        ("quadratic", PolynomialFeatures(degree=2, include_bias=False)),
        ("smooth", SplineTransformer(n_knots=5, degree=3, include_bias=False,
                                     extrapolation="linear")),
    ])
    steps.insert(-1, ("features", basis))
    steps.insert(-1, ("feature_scale", StandardScaler()))
    return Pipeline(steps)

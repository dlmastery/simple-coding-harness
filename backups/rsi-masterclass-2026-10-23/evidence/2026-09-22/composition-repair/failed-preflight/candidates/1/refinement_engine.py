"""Refine a template relative to its settings; keep the frozen v1 builder intact."""
import hashlib
import math

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import (
    ExtraTreesClassifier, ExtraTreesRegressor, RandomForestClassifier, RandomForestRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
)

from study_engine import build_recipe as legacy_build


def build_recipe(schema, kind, template, factor, seed=41):
    if not .05 <= factor <= 20:
        raise ValueError("Capacity factor outside declared domain")
    model = legacy_build(schema, kind, template, 1., seed)
    if factor == 1:
        return model
    pipeline = model.regressor if isinstance(model, TransformedTargetRegressor) else model
    learner = pipeline.named_steps["model"]
    if isinstance(learner, (ExtraTreesClassifier, ExtraTreesRegressor, RandomForestClassifier, RandomForestRegressor)):
        # A depth cap is new for an unlimited template; its finite reference is
        # explicit. Leaf refinement starts from the actual template leaf size.
        depth_reference = learner.max_depth if learner.max_depth is not None else 8
        learner.set_params(max_depth=max(2, min(32, round(depth_reference*factor))),
                           min_samples_leaf=max(1, min(30, round(learner.min_samples_leaf/factor))))
    elif isinstance(learner, (HistGradientBoostingClassifier, HistGradientBoostingRegressor)):
        leaf_reference = learner.max_leaf_nodes if learner.max_leaf_nodes is not None else 31
        learner.set_params(max_leaf_nodes=max(7, min(63, round(leaf_reference*factor))),
                           l2_regularization=learner.l2_regularization/factor)
    else:
        return legacy_build(schema, kind, template, factor, seed)
    return model


def constructor_description(value):
    """Canonical constructor identity for this supported sklearn builder set.

    This identifies settings, not learned state or mathematical equivalence.
    Unsupported parameter types fail instead of falling back to object repr.
    """
    if isinstance(value, BaseEstimator):
        cls = type(value)
        return ("estimator", cls.__module__, cls.__qualname__,
                tuple((key, constructor_description(item)) for key, item in sorted(value.get_params(deep=False).items())))
    if isinstance(value, np.generic):
        return constructor_description(value.item())
    if isinstance(value, np.ndarray):
        return ("array", str(value.dtype), value.shape, constructor_description(value.tolist()))
    if isinstance(value, dict):
        return ("dict", tuple(sorted((constructor_description(key), constructor_description(item)) for key, item in value.items())))
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(constructor_description(item) for item in value))
    if value is None or isinstance(value, (str, bool, int)):
        return (type(value).__name__, value)
    if isinstance(value, float):
        return ("float", "nan" if math.isnan(value) else value.hex())
    if isinstance(value, slice):
        return ("slice", constructor_description((value.start, value.stop, value.step)))
    if callable(value) and getattr(value, "__name__", None):
        return ("callable", getattr(value, "__module__", type(value).__module__),
                getattr(value, "__qualname__", value.__name__))
    raise TypeError(f"Unsupported constructor parameter: {type(value).__name__}")


def constructor_signature(model):
    return hashlib.sha256(repr(constructor_description(model)).encode("utf-8")).hexdigest()


def admit_distinct(schema, kind, proposals, seen_signatures=(), seed=41):
    """Inspect an already bounded proposal list, without fitting or replenishing it."""
    seen = set(seen_signatures)
    accepted, refused = [], []
    for proposal in proposals:
        model = build_recipe(schema, kind, proposal["template"], proposal["factor"], seed)
        signature = constructor_signature(model)
        record = dict(proposal, constructor_sha256=signature)
        if signature in seen:
            refused.append(dict(record, reason="same-constructor"))
        else:
            seen.add(signature)
            accepted.append(record)
    return accepted, refused

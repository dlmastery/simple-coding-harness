"""Build a parameterized child of an explicitly versioned development template."""
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import (ExtraTreesClassifier, ExtraTreesRegressor,
                              RandomForestClassifier, RandomForestRegressor,
                              HistGradientBoostingClassifier, HistGradientBoostingRegressor)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR

from parent_engine import build as parent_build
from revision_one_engine import build as first_build
from revision_two_engine import build as second_build


def build_recipe(schema, kind, template, factor, seed=41):
    if not .05 <= factor <= 20:
        raise ValueError("Capacity factor outside frozen domain")
    generation, name = template.split(":", 1)
    builder = {"base": parent_build, "one": first_build, "two": second_build}[generation]
    model = builder(schema, kind, name, seed)
    if factor == 1:
        return model
    pipeline = model.regressor if isinstance(model, TransformedTargetRegressor) else model
    learner = pipeline.named_steps["model"]
    if isinstance(learner, (SVC, SVR, LogisticRegression)):
        learner.set_params(C=min(10000., max(.001, learner.C * factor)))
    elif isinstance(learner, Ridge):
        learner.set_params(alpha=min(10000., max(.001, learner.alpha / factor)))
    elif isinstance(learner, (ExtraTreesClassifier, ExtraTreesRegressor, RandomForestClassifier, RandomForestRegressor)):
        learner.set_params(max_depth=max(2, min(32, round(8*factor))),
                           min_samples_leaf=max(1, min(30, round(3/factor))))
    elif isinstance(learner, (HistGradientBoostingClassifier, HistGradientBoostingRegressor)):
        learner.set_params(max_leaf_nodes=max(7, min(63, round(31*factor))), l2_regularization=1/factor)
    elif isinstance(learner, (KNeighborsClassifier, KNeighborsRegressor)):
        learner.set_params(n_neighbors=max(2, min(100, round(learner.n_neighbors/factor))))
    else:
        raise ValueError("This template has no declared capacity refinement")
    return model

"""Agent-authored objective/scaling changes; preserve the conventional parent."""
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

from parent_engine import build as parent_build


def build(schema, kind, candidate, seed=41):
    if kind == "classification":
        if candidate == "rbf-unscaled":
            model = parent_build(schema, kind, "rbf-10", seed)
            for name, transform, columns in model.named_steps["prepare"].transformers:
                if name == "numeric":
                    transform.set_params(scale="passthrough")
            return model
        if candidate == "rbf-wide":
            model = parent_build(schema, kind, "rbf-10", seed)
            count = int((schema.role == "feature").sum())
            model.set_params(model__gamma=.25 / count)
            return model
        if candidate == "extra-leaf2":
            model = parent_build(schema, kind, "extra-trees", seed)
            model.set_params(model__min_samples_leaf=2)
            return model
        if candidate == "boost-regularized":
            model = parent_build(schema, kind, "hist-boost", seed)
            model.set_params(model__max_leaf_nodes=15, model__learning_rate=.05,
                             model__max_iter=300, model__l2_regularization=5.)
            return model
    elif kind == "regression":
        model = parent_build(schema, kind, "rbf-1", seed)
        if candidate == "median-reference":
            model.regressor.set_params(model=DummyRegressor(strategy="median"))
        elif candidate == "absolute-boost":
            model.regressor.set_params(model=HistGradientBoostingRegressor(
                loss="absolute_error", max_iter=300, learning_rate=.05,
                max_leaf_nodes=15, l2_regularization=1., early_stopping=False, random_state=seed))
        elif candidate == "absolute-forest":
            model.regressor.set_params(model=RandomForestRegressor(
                criterion="absolute_error", n_estimators=64, min_samples_leaf=3, n_jobs=1, random_state=seed))
        elif candidate == "svr-tight":
            model.regressor.set_params(model__epsilon=.01)
        else:
            raise ValueError(candidate)
        return model
    raise ValueError((kind, candidate))

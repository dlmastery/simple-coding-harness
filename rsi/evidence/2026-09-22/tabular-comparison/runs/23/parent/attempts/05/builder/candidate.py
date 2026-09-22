from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'base:rbf-1', 0.3, seed)

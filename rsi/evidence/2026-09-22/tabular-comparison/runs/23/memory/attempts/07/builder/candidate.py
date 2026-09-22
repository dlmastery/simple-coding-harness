from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'two:unscaled-c1', 1.0, seed)

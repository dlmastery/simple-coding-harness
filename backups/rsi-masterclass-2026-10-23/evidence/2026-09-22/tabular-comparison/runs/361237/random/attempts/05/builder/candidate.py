from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'two:quadratic-splines', 0.13144368, seed)

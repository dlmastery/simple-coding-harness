from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'two:log-boost', 0.13068133, seed)

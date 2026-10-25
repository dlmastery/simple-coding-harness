from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:boost-regularized', 0.44100938, seed)

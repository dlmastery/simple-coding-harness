from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:rbf-unscaled', 0.16840088, seed)

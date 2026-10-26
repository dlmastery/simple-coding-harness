from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:absolute-boost', 0.33410788, seed)

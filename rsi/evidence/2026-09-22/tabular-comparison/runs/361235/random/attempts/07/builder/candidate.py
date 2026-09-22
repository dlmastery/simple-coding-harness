from study_engine import build_recipe


def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'two:log-svr', 9.38397621, seed)

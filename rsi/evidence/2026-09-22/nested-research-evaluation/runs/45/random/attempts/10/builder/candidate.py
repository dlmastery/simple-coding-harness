from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'one:boost-regularized', 1.26597134, seed)

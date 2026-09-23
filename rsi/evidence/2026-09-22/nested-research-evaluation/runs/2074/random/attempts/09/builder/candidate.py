from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'base:neighbors-5', 0.3171531, seed)

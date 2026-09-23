from refinement_engine import build_recipe

def build(schema, kind, seed=41):
    return build_recipe(schema, kind, 'two:native-category-boost', 1.0, seed)

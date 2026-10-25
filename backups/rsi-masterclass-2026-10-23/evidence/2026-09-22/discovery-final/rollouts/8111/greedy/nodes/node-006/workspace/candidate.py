from engine import build as build_pipeline

FAMILY = 'boost'
TRANSFORM = 'quadratic'
STRENGTH = 3.0
STAGE = 3

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)

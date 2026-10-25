from engine import build as build_pipeline

FAMILY = 'boost'
TRANSFORM = 'quadratic'
STRENGTH = 6.75
STAGE = 7

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)

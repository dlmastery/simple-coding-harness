from engine import build as build_pipeline

FAMILY = 'linear'
TRANSFORM = 'quadratic'
STRENGTH = 0.30000000000000004
STAGE = 4

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)

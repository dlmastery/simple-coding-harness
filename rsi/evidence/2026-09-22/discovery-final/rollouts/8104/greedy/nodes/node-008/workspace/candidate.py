from engine import build as build_pipeline

FAMILY = 'linear'
TRANSFORM = 'quadratic'
STRENGTH = 0.15000000000000002
STAGE = 5

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)

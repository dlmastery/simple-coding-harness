from engine import build as build_pipeline

FAMILY = 'linear'
TRANSFORM = 'quadratic'
STRENGTH = 0.22500000000000003
STAGE = 7

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)

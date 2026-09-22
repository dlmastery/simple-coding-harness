from engine import build as build_pipeline

FAMILY = 'extra'
TRANSFORM = 'pairwise'
STRENGTH = 1.0
STAGE = 1

def build(kind, seed):
    return build_pipeline(kind, FAMILY, TRANSFORM, STRENGTH, seed)

"""Inherited simple improver: revise the first local-refinement multiplier."""
from improver import rewrite


def generate(parent, evidence, generation, rejected, destination):
    return rewrite(parent, evidence, "i0", generation, rejected, destination)

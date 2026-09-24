"""Revised improver: preserve coverage and rewrite allocation and parent selection."""
from improver import rewrite


def generate(parent, evidence, generation, rejected, destination):
    return rewrite(parent, evidence, "i1", generation, rejected, destination)

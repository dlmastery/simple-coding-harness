"""Step 05 - a meta skill generates the graph harness, under human approval:
boot skills/graph-writer, read the graph as a node / edge list, answer
y / n / edit, then run the generated pack on Adult.

    FAKE_MODEL=1 python run.py                    # the fake writer; you answer at the prompt
    FAKE_MODEL=1 HUMAN=script:y python run.py     # a scripted yes
    python run.py                                 # the real model: BASE_URL / API_KEY / MODEL
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

WRITER = "graph-writer"


def step03():
    """Step 03's runner, loaded under its own name: the generate / run sequence is the same, only the writer differs."""
    spec = importlib.util.spec_from_file_location("step03_run", HERE.parent / "step_03_meta_generates_loop" / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_graph(model, out_dir, human=None, quiet=False):
    return step03().generate(model, out_dir, human=human, quiet=quiet, writer=WRITER, step=HERE)


if __name__ == "__main__":
    step03().main(writer=WRITER, step=HERE, generated="adult-income-graph")

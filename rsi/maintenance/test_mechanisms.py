import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("mechanisms", Path(__file__).resolve().parents[1] / "tools/mechanisms.py")
mechanisms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mechanisms)


def test_teaching_mechanisms_reject_invalid_cases(tmp_path):
    assert mechanisms.run_checks(tmp_path) > 0


def test_cycles_are_not_valid_topological_orders():
    assert not mechanisms.order_is_valid(["a", "b"], {"a": ["b"], "b": ["a"]})


def test_duplicate_replay_does_not_mint_new_evidence():
    tree = {"root": {"parent": None, "cost": 1, "score": 3}}
    outcomes, cost = mechanisms.replay(tree, ["root", "root"], 5)
    assert outcomes[-1] == ("root", "duplicate", None)
    assert cost == 1

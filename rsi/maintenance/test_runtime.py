"""Behavioral checks for the small public teaching runtime."""
import importlib.util
import sys
import subprocess
from pathlib import Path

import numpy as np
import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools/lab.py"
spec = importlib.util.spec_from_file_location("rsi_lab", TOOLS)
lab = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lab
spec.loader.exec_module(lab)


def test_source_and_chronological_boundaries():
    data = lab.read_data("bike")
    assert len(data) == 17379
    assert (data.casual + data.registered == data.cnt).all()
    splits = lab.partitions(data, "bike")
    assert np.all(sum(mask.astype(int) for mask in splits.values()) == 1)
    assert data.loc[splits["train"], "dteday"].max() < data.loc[splits["selection"], "dteday"].min()
    assert data.loc[splits["selection"], "dteday"].max() < data.loc[splits["final"], "dteday"].min()
    with pytest.raises(lab.Refusal, match="forbidden"):
        lab.feature_names("bike", "casual,registered", data)


def test_wine_identical_inputs_never_cross_partitions():
    data = lab.read_data("wine")
    assert len(data) == 1599
    keys = data.drop(columns="quality").astype(str).agg("|".join, axis=1)
    splits = lab.partitions(data, "wine")
    groups = [set(keys[mask]) for mask in splits.values()]
    assert not groups[0] & groups[1] and not groups[0] & groups[2] and not groups[1] & groups[2]
    assert all(lab.target(data, "wine")[mask].nunique() == 2 for mask in splits.values())


def test_preprocessing_is_fit_only_on_training_values():
    data = lab.read_data("bike")
    masks = lab.partitions(data, "bike")
    pipe = lab.pipeline("bike", "linear", ["temp", "hr"], 17)
    pipe.fit(data.loc[masks["train"], ["temp", "hr"]], data.loc[masks["train"], "cnt"])
    scaler = pipe.named_steps["prepare"].named_transformers_["numeric"].named_steps["scale"]
    assert scaler.mean_[0] == pytest.approx(data.loc[masks["train"], "temp"].mean())
    assert scaler.mean_[0] != pytest.approx(data.temp.mean())


def test_failed_attempts_count_and_contract_cannot_change(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "MAX_ATTEMPTS", 2)
    with pytest.raises(lab.Refusal):
        lab.experiment(tmp_path, "bike", "constant", "casual", 17, "Try leaked features")
    assert lab.records(tmp_path)[0]["status"] == "failed"
    lab.experiment(tmp_path, "bike", "constant", "all", 17, "Use training median")
    with pytest.raises(lab.Refusal, match="budget"):
        lab.experiment(tmp_path, "bike", "linear", "all", 17, "Another attempt")
    (tmp_path / "CONTRACT.md").write_text("A more convenient metric", encoding="utf-8")
    with pytest.raises(lab.Refusal, match="contract"):
        lab.experiment(tmp_path, "bike", "constant", "all", 17, "Altered contract")


def test_final_refits_selected_recipe_and_closes_search(tmp_path):
    row = lab.experiment(tmp_path, "bike", "constant", "all", 17, "Training median baseline")
    assert lab.compare(tmp_path) == row["candidate"]
    measured = lab.final_evaluation(tmp_path, row["candidate"])
    data = lab.read_data("bike")
    splits = lab.partitions(data, "bike")
    expected = abs(data.loc[splits["final"], "cnt"] - data.loc[splits["train"], "cnt"].median()).mean()
    assert measured == pytest.approx(expected)
    with pytest.raises(lab.Refusal, match="closed"):
        lab.experiment(tmp_path, "bike", "linear", "all", 17, "Try after seeing final")
    with pytest.raises(lab.Refusal, match="closed"):
        lab.final_evaluation(tmp_path, row["candidate"])


def test_interrupted_attempt_is_not_silently_resumed(tmp_path):
    lab.check_contract(tmp_path, "bike")
    row = dict.fromkeys(lab.FIELDS, "")
    row.update(candidate="trial-001", status="running", seconds=0)
    lab.save_records(tmp_path, [row])
    with pytest.raises(lab.Refusal, match="Interrupted"):
        lab.experiment(tmp_path, "bike", "constant", "all", 17, "Resume")


def test_domain_rules_reject_semantic_errors(tmp_path):
    source = tmp_path / "domain.md"
    lab.write(source, "| Subject | Relation | Object |\n|---|---|---|\n| model | uses feature | component |\n| component | derived from | target |\n| scaler | fit on | final |\n| search | selects on | final |\n")
    errors = lab.audit_domain(source, tmp_path / "check.md")
    assert len(errors) == 3


def test_workspace_lock_blocks_concurrent_writers(tmp_path):
    with lab.workspace_lock(tmp_path):
        with pytest.raises(lab.Refusal, match="busy"):
            with lab.workspace_lock(tmp_path):
                pass
    assert not (tmp_path / ".running").exists()


def test_lesson_budget_survives_new_cli_processes(tmp_path):
    def invoke(*arguments):
        return subprocess.run([sys.executable, str(TOOLS), *map(str, arguments)],
                              capture_output=True, text=True, timeout=60)

    first = invoke("run", "--workspace", tmp_path, "--attempt-limit", 1,
                   "--model", "constant", "--hypothesis", "One-fit lesson")
    assert first.returncode == 0, first.stderr
    compared = invoke("compare", "--workspace", tmp_path)
    assert compared.returncode == 0, compared.stderr
    assert "Attempts: 1 / 1" in (tmp_path / "COMPARISON.md").read_text(encoding="utf-8")
    exhausted = invoke("run", "--workspace", tmp_path, "--model", "linear",
                       "--hypothesis", "Attempt after restart")
    assert exhausted.returncode == 2 and "budget exhausted" in exhausted.stderr
    changed = invoke("run", "--workspace", tmp_path, "--attempt-limit", 2,
                     "--hypothesis", "Try to increase the budget")
    assert changed.returncode == 2 and "cannot change" in changed.stderr
    assert len(lab.records(tmp_path)) == 1
    contract = tmp_path / "CONTRACT.md"
    contract.write_text(contract.read_text(encoding="utf-8").replace("max_attempts: 1", "max_attempts: 12"), encoding="utf-8")
    modified = invoke("compare", "--workspace", tmp_path)
    assert modified.returncode == 2 and "integrity" in modified.stderr

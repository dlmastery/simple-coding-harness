import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_result

SOURCE = Path(__file__).resolve().parents[1] / "evidence/2026-09-20/walkthrough/02-01-model-change"


@pytest.fixture
def candidate(tmp_path):
    workspace = tmp_path / "run"
    shutil.copytree(SOURCE, workspace)
    return workspace / "trial-001"


def test_valid_result_recomputes(candidate):
    assert check_result.check(candidate) == pytest.approx(159.94791188618632)


def test_false_summary_is_rejected(candidate):
    report = candidate / "RESULT.md"
    report.write_text(report.read_text(encoding="utf-8").replace("159.947912", "10.000000"), encoding="utf-8")
    with pytest.raises(ValueError, match="Report score"):
        check_result.check(candidate)


def test_wrong_partition_row_is_rejected(candidate):
    path = candidate / "predictions.csv"
    rows = pd.read_csv(path)
    rows.loc[0, "source_row"] = 0
    rows.to_csv(path, index=False)
    with pytest.raises(ValueError, match="row identities"):
        check_result.check(candidate)


def test_changed_actual_label_is_rejected(candidate):
    path = candidate / "predictions.csv"
    rows = pd.read_csv(path)
    rows.loc[0, "actual"] += 1
    rows.to_csv(path, index=False)
    with pytest.raises(ValueError, match="actual targets"):
        check_result.check(candidate)

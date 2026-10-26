"""MLE-bench competitions: where they live, and how a submission is graded.

The course uses seven CPU-friendly competitions from MLE-bench Lite
(github.com/openai/mle-bench). MLE-bench prepares each one from Kaggle into

    <data>/<id>/prepared/public/    what the agent sees: description, train, test
    <data>/<id>/prepared/private/   test answers: only the grader reads these

and grades with the competition's own metric. On top of the raw score we
report where it would have ranked on the real Kaggle leaderboard: the
fraction of human teams it beats. That makes scores comparable across
competitions with different metrics, the way MLE-bench's medal rates do.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DATA = Path(os.environ.get("MLEBENCH_DATA", Path.home() / "rsi-data" / "mlebench"))

SPLITS = {
    # evolve: the only competitions an improver may look at while it edits the harness
    "evolve": ["spooky-author-identification", "nomad2018-predict-transparent-conductors", "leaf-classification"],
    # heldout: same kinds of problem (short-text classification, small tabular), new competitions
    "heldout": ["detecting-insults-in-social-commentary", "tabular-playground-series-may-2022"],
    # ood: different structure (JSON records with text and metadata; multi-label text at 160k rows)
    "ood": ["random-acts-of-pizza", "jigsaw-toxic-comment-classification-challenge"],
}
ALL = [c for split in SPLITS.values() for c in split]


@dataclass
class Competition:
    id: str
    public: Path
    lower_is_better: bool
    description: str


def _registry_comp(cid):
    from mlebench.registry import Registry
    return Registry(DATA).get_competition(cid)


def get(cid):
    from mlebench.grade import get_leaderboard
    comp = _registry_comp(cid)
    lower = comp.grader.is_lower_better(get_leaderboard(comp))
    return Competition(cid, comp.public_dir, lower, comp.description)


def grade(cid, submission_csv):
    """Grade one submission with MLE-bench, then place it on the human leaderboard."""
    from mlebench.grade import get_leaderboard, grade_csv
    comp = _registry_comp(cid)
    report = grade_csv(Path(submission_csv), comp)
    out = {"score": report.score, "valid": report.valid_submission, "beats_forest": bool(report.above_median),
           "norm": 0.0}
    if report.score is not None:
        board = get_leaderboard(comp)["score"].dropna()
        worse = (board > report.score) if report.is_lower_better else (board < report.score)
        out["norm"] = float(worse.mean())
    return out


def obfuscated_description(cid):
    """MLE-bench's rewritten description: same task, no competition name or Kaggle history.

    Lab 05 uses it as a counterfactual: a harness whose gain depends on recognizing
    the competition loses that gain here (the CHASE idea, arXiv 2609.18366).
    """
    import mlebench
    p = Path(mlebench.__file__).parent / "competitions" / cid / "description_obfuscated.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""

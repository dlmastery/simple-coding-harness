"""Step 00 - the locked test: the test split is scored once, through this object,
and a second call raises. It is the anti-peek gate: a search loop that could
score the test split twice could tune on it.
"""


class TestAlreadyScored(RuntimeError):
    pass


class LockedTest:
    def __init__(self, score):
        self._score = score   # score(recipe) -> AUC on the test split; the gate is its only holder
        self.result = None

    def score_once(self, recipe):
        if self.result is not None:
            raise TestAlreadyScored("the test split was scored once already; there is no second look")
        self.result = {"recipe": recipe, "test_auc": self._score(recipe)}
        return self.result["test_auc"]

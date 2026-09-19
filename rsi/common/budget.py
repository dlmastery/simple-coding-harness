"""Step 00 - the budget: n fits, then it raises. The loop has no other way to fit.

An off switch that is an object, not a sentence in a README: a policy that wants
a 25th fit gets BudgetExhausted, and `used` is the count every claim quotes.
"""


class BudgetExhausted(RuntimeError):
    pass


class Budget:
    def __init__(self, n):
        self.n = n
        self.used = 0

    @property
    def left(self):
        return self.n - self.used

    def fit(self, fn, *args):
        """The one path to a fit: count first, then call. An exhausted budget refuses."""
        if self.used >= self.n:
            raise BudgetExhausted(f"budget of {self.n} fits used; fit {self.used + 1} refused")
        self.used += 1
        return fn(*args)

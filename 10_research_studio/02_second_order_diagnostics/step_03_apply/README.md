# 10.08 · Apply to Debugging Task

**Purpose:** Use SO-RSI principles on your own debugging workflow.

## Your Task

Apply SO-RSI to a simple debugging scenario:
- You have a failing test
- You try several fixes
- Some fail repeatedly

## Steps

1. Define a simple failing test (e.g., function returns wrong value)
2. Attempt 3-5 fixes manually
3. For each attempt, record:
   - What you changed
   - What happened
   - What you expected
4. After all attempts, analyze:
   - Did you repeat the same fix? (recurrence)
   - Did you undo previous changes? (opposing)
   - Did outcomes surprise you? (mismatch)
5. For each anomaly, identify the root cause

## Simplified Example

```python
# Failing test
def test_add():
    assert add(2, 3) == 5  # Currently fails

# Attempt 1: Fix parameter order
def add(a, b): return b + a  # Still fails

# Attempt 2: Change to subtraction
def add(a, b): return a - b  # Still fails

# Attempt 3: Go back to original
def add(a, b): return a + b  # Still fails

# Analysis: Recurrence (attempt 3 = original), opposing (2 undoes 1)
# Root cause: Test setup wrong, not function
```

## Expected Outcome

You should observe:
- Retrospective analysis reveals patterns you missed in the moment
- Diagnostic questions help identify root causes
- Second-order thinking prevents thrashing

## Quiz

**Q1:** How does SO-RSI differ from standard debugging?

**A1:** Standard debugging often patches symptoms (change code, test, repeat). SO-RSI asks WHY the symptom occurred, detecting patterns (recurrence, opposing, mismatch) that indicate deeper issues.

**Q2:** Can SO-RSI be automated for real debugging tools?

**A2:** Partially. Anomaly detection on execution traces is automatable. Diagnostic probes require domain knowledge. A practical system might detect anomalies and prompt the developer with diagnostic questions.

## Next Step

[Group 03 · Scaling RSI: Coordination & Swarms](../03_scaling_coordination/README.md)

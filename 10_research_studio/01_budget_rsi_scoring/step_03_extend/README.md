# 10.05 · Extend to Your Own Edits

**Purpose:** Apply the scorer to a new code editing task.

## Your Task

Adapt the Budget RSI scorer to a simple code editing task of your choice:
- Fixing bugs in a small function
- Optimizing a loop
- Adding error handling
- Refactoring code

## Steps

1. Define your task (e.g., "add error handling to function X")
2. Generate 5-10 proposed edits (manually or via simple rules)
3. Extract diff features for each edit
4. Train scorer on a subset (e.g., 3 edits evaluated)
5. Score remaining edits and select best
6. Evaluate selected edit and compare to random selection

## Simplified Approach

For a quick extension, use the demo's synthetic generation but:
- Change the feature generation to match your task
- Use a smaller dataset (10-20 edits)
- Manually define "success" criteria

## Expected Outcome

You should observe:
- Scorer selects better edits than random (if features correlate with quality)
- Training set size affects scorer quality
- Feature choice matters for your specific task

## Quiz

**Q1:** What happens if your task's success is not correlated with the diff features?

**A1:** The scorer will perform no better than random. This highlights that feature engineering is critical—the features must capture what actually matters for your specific task.

**Q2:** Can Budget RSI work for non-code tasks?

**A2:** Yes, if you can define: (1) a steering split for evaluation, (2) extractable features from proposed changes, and (3) a correlation between features and quality. The mechanism is general.

## Next Step

[Group 02 · Second-Order RSI: Diagnostic Inquiry](../02_second_order_diagnostics/README.md)

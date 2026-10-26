# 10.04 · Analyze the Scoring Mechanism

**Purpose:** Understand how linear readout scoring works.

## What This Lab Teaches

The Budget RSI mechanism relies on three key ideas:

### 1. Steering Split

Instead of evaluating all test instances, reserve a subset (e.g., 48/164) for scoring. This split:
- Provides a proxy for held-out performance
- Avoids contaminating the final evaluation
- Enables cheap pre-selection

### 2. Diff Features

The paper extracts 8 coordinates from each code diff:
- Lines added
- Lines deleted
- Files changed
- Files added
- Files removed
- Import changes
- Function additions
- Function deletions

These features capture the nature of the edit without running it.

### 3. Linear Readout

The scorer uses a simple linear model:
```
score = w0 * parent_rate + w1 * feature1 + ... + w8 * feature8
```

Why linear?
- Fast to train (96 edits × 9 features)
- Fast to score (multiply-add per edit)
- Interpretable (coefficients show feature importance)

## Your Task

1. Modify the demo to print the learned coefficients
2. Rank features by absolute coefficient value
3. Explain which features matter most and why

## Code Modification

Add this to `demo.py` after training:

```python
# After training, analyze coefficients
feature_names = ['parent_rate', 'lines_added', 'lines_deleted', 
                 'files_changed', 'files_added', 'files_removed',
                 'import_changes', 'func_additions', 'func_deletions']
feature_importance = list(zip(feature_names, scorer.coefficients))
feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

print("\nFeature Importance:")
for name, coeff in feature_importance:
    print(f"  {name:20s}: {coeff:+.3f}")
```

## Expected Output

Features ranked by importance. In synthetic data, results will vary, but you should see:
- Some features have large coefficients (strong influence)
- Some features have near-zero coefficients (weak influence)
- Parent rate often has significant weight

## Quiz

**Q1:** Why use a linear model instead of a more complex one like a neural network?

**A1:** Because the goal is fast scoring, not maximum accuracy. A linear model trains in milliseconds and scores in microseconds. More complex models would add overhead without necessarily improving selection quality for this task.

**Q2:** What happens if two features are highly correlated?

**A2:** The linear model will split importance between them, making coefficients harder to interpret. However, the combined predictive power remains. Feature selection or regularization could address this in a production system.

## Next Step

[10.05 · Extend to your own edits](../step_03_extend/README.md)

# 10.03 · Run the Budget RSI Demo

**Purpose:** Execute the laptop demo to see the mechanism in action.

## Instructions

1. Navigate to the demo:
```bash
cd ../../12_october_2026_papers/01_budget_rsi
python demo.py
```

2. Observe the output showing:
   - Generation of 128 synthetic code edits
   - Training the linear readout scorer
   - Comparison of three selection strategies
   - Cost savings demonstration

## What to Observe

**Training phase:**
- How many edits are used for training? (96)
- What features are used? (parent_rate + 8 diff features)
- How are coefficients learned? (linear regression)

**Selection comparison:**
- Budget RSI vs parent-rate ablation vs random
- Which strategy achieves the best held-out score?
- How much improvement over random baseline?

**Cost analysis:**
- Full evaluation cost in time
- Budget RSI cost in time
- Percentage reduction

## Expected Observations

- Budget RSI should outperform random selection
- Budget RSI should outperform parent-rate ablation
- Cost reduction should be ~80-90%
- Runtime should be < 5 minutes

## Check Your Understanding

1. Why does the paper use a steering split instead of training on all test data?
2. What happens if you change the number of diff features from 8 to 4?
3. How does the scorer's performance change with fewer training edits?

## Quiz

**Q1:** What is the purpose of the steering split?

**A1:** To evaluate edits without touching the final held-out test set. This allows scoring and selection while preserving a clean evaluation boundary.

**Q2:** Why does the demo use synthetic edits instead of real code diffs?

**A2:** To make the demo laptop-executable without requiring access to GPT-4o, the full HumanEval+ dataset, or complex diff parsing tools. The mechanism is preserved even with synthetic data.

## Next Step

[10.04 · Analyze the scoring mechanism](../step_02_analyze_mechanism/README.md)

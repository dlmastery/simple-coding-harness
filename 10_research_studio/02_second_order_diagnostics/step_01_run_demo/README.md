# 10.06 · Run the SO-RSI Demo

**Purpose:** Execute the laptop demo to see anomaly detection in action.

## Instructions

1. Navigate to the demo:
```bash
cd ../../12_october_2026_papers/02_second_order_rsi
python demo.py
```

2. Observe the output showing:
   - Naive RSI vs SO-RSI comparison
   - Anomaly detection in action
   - Diagnostic probe results

## What to Observe

**Naive RSI (first-order):**
- Attempts fixes without diagnostics
- Success rate around 30% (in demo)
- No understanding of why fixes fail

**SO-RSI (second-order):**
- Detects anomalies before attempting fixes
- Success rate around 50% (in demo)
- Runs diagnostic probes to understand root causes

**Anomaly types detected:**
- Recurrence: Same fix attempted repeatedly
- Opposing: Undoing previous changes
- Mismatch: Expected vs actual outcome differs

## Expected Observations

- SO-RSI should outperform Naive RSI by ~20 percentage points
- Diagnostics should trigger 3-5 times in 20 attempts
- Each diagnostic should provide a specific recommendation

## Check Your Understanding

1. Why does detecting recurrence improve success rate?
2. What's the difference between first-order and second-order optimization?
3. How does inquiry memory help across RSI rounds?

## Quiz

**Q1:** What is the key difference between Naive RSI and SO-RSI?

**A1:** Naive RSI patches symptoms (first-order), while SO-RSI investigates root causes (second-order) before making changes. SO-RSI detects structural anomalies and runs diagnostic probes to understand WHY failures occur.

**Q2:** Why does the demo use synthetic execution traces?

**A2:** To demonstrate the mechanism without requiring Lean 4, Verus, or complex formal verification setups. The anomaly detection logic is preserved even with synthetic traces.

## Next Step

[10.07 · Analyze diagnostic probes](../step_02_analyze_probes/README.md)

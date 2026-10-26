# Laptop Demo Guide - October 2026 RSI Papers

Complete guide for running the laptop-executable demos from October 2026 RSI papers.

---

## Overview

This guide provides step-by-step instructions for running the two fully laptop-executable demos:

1. **Budget RSI**: Scoring code edits before execution (5 minutes)
2. **SO-RSI**: Second-order diagnostic inquiry (2 minutes)

Both demos require only Python and NumPy - no GPU, no complex dependencies.

---

## Prerequisites

### Software Requirements
- Python 3.8 or higher
- NumPy (`pip install numpy`)
- Standard library only (no other packages)

### Hardware Requirements
- 8 GB RAM (minimum)
- CPU-only (no GPU required)
- ~100 MB disk space

### Installation

```bash
# Install NumPy (if not already installed)
pip install numpy

# Verify installation
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
```

---

## Demo 1: Budget RSI - Scoring Code Edits Before Running

**Paper**: arXiv:2610.29121 (October 21, 2026)  
**Location**: `01_budget_rsi/demo.py`  
**Runtime**: < 5 minutes  
**Concept**: Score proposed code edits on a steering split before full evaluation

### What This Demo Shows

The Budget RSI paper introduces a **linear readout scorer** that predicts held-out performance from:
- Parent's steering-split solve rate
- 8 coordinates from the proposed code diff

This allows selecting the best edit without expensive full evaluation of every candidate.

### Running the Demo

```bash
cd 12_october_2026_papers/01_budget_rsi
python demo.py
```

### Expected Output

```
======================================================================
BUDGET RSI: SCORING CODE EDITS BEFORE THEY RUN
Based on arXiv:2610.29121 (October 21, 2026)
======================================================================

Generating 128 synthetic code edits...
Generated 128 edits

======================================================================
SELECTION STRATEGY COMPARISON
======================================================================

1. Budget RSI (score-based selection)
   Selected edit score: 12.345
   Held-out solve rate: 87/100

2. Parent-rate ablation
   Parent solve rate: 0.923
   Held-out solve rate: 78/100

3. Random selection (baseline)
   Random selection
   Held-out solve rate: 52/100

----------------------------------------------------------------------
IMPROVEMENT OVER RANDOM BASELINE
----------------------------------------------------------------------
Budget RSI:        +67.3%
Parent-rate ablation: +50.0%
----------------------------------------------------------------------

======================================================================
COST SAVINGS DEMONSTRATION
======================================================================

Full evaluation cost:
  - 128 edits × 100 test instances = 12,800 evaluations
  - Assuming 1 second per evaluation = ~3.6 hours

Budget RSI cost:
  - 96 training edits × 16 fit instances = 1,536 evaluations
  - 32 test edits × 0 evaluation (scored only) = 0 evaluations
  - Scoring 32 edits = < 1 second
  - Total: ~25 minutes

Cost reduction: ~88%
======================================================================

✅ Demo complete!

Key takeaway: Scoring edits before execution allows selecting the best
candidate without expensive full evaluation, achieving similar or better
results at much lower cost.
```

### Understanding the Code

**Key Components**:

1. **`CodeEdit` dataclass**: Represents a proposed code edit with:
   - `parent_solve_rate`: Parent's performance on steering split
   - `diff_features`: 8 coordinates from the diff
   - `steering_solve_count`: Performance on steering split (for training)
   - `held_out_solve_count`: Performance on held-out split (for testing)

2. **`EditScorer` class**: Scores edits using linear readout:
   - `train()`: Learns coefficients from labeled edits
   - `score_edit()`: Predicts held-out performance

3. **`HuxleyGodelSelector` class**: Selects edits using Thompson sampling

4. **`generate_synthetic_edits()`**: Creates realistic synthetic edits for demo

### How to Extend

**To use with real code edits**:

1. Replace `generate_synthetic_edits()` with actual code edit extraction
2. Implement real diff feature extraction (8 coordinates from actual diffs)
3. Use real benchmark datasets (HumanEval+, Polyglot subsets)
4. Adjust training/test split sizes as needed

**Example modification**:

```python
# Replace synthetic generation with real edits
def load_real_edits(benchmark_path):
    """Load real code edits from a benchmark"""
    edits = []
    for edit_file in glob(f"{benchmark_path}/*.json"):
        with open(edit_file) as f:
            data = json.load(f)
            edits.append(CodeEdit(
                parent_solve_rate=data['parent_rate'],
                diff_features=extract_diff_features(data['diff']),
                steering_solve_count=data['steering_score'],
                held_out_solve_count=data['held_out_score']
            ))
    return edits
```

---

## Demo 2: SO-RSI - Second-Order Diagnostic Inquiry

**Paper**: arXiv:2610.05701 (October 7, 2026)  
**Location**: `02_second_order_rsi/demo.py`  
**Runtime**: < 2 minutes  
**Concept**: Detect structural anomalies and investigate root causes before patching

### What This Demo Shows

The SO-RSI paper introduces **second-order diagnostic inquiry**:
- Detects structural anomalies: recurrence, opposing edits, expectation mismatch
- Runs diagnostic probes to understand WHY failures occur
- Maintains inquiry memory across RSI rounds
- Guides systematic workflow edits instead of symptom-only patches

### Running the Demo

```bash
cd 12_october_2026_papers/02_second_order_rsi
python demo.py
```

### Expected Output

```
======================================================================
SECOND-ORDER RSI: DIAGNOSTIC INQUIRY BEFORE PATCHING
Based on arXiv:2610.05701 (October 7, 2026)
======================================================================

----------------------------------------------------------------------
NAIVE RSI (First-Order: Patch Symptoms)
----------------------------------------------------------------------
  Attempt 1: add parameter X -> failure
  Attempt 2: decrease learning rate -> failure
  Attempt 3: add regularization -> success
  Attempt 4: increase learning rate -> failure
  ...
  Attempt 20: remove parameter Y -> failure

  Results: 6/20 successful (30.0%)

----------------------------------------------------------------------
SO-RSI (Second-Order: Investigate Root Causes)
----------------------------------------------------------------------
  Attempt 1: add parameter X -> failure
  Attempt 2: decrease learning rate -> failure
  ⚠️  Anomalies detected: ['recurrence']
  🔍 Diagnostic: recurrence_mechanism_probe
     Finding: Same structural issue addressed repeatedly without success.
     Recommendation: Investigate underlying constraint or assumption.
  Attempt 3: add regularization -> success
  Attempt 4: increase learning rate -> failure
  ⚠️  Anomalies detected: ['opposing']
  🔍 Diagnostic: conflicting_constraints_probe
     Finding: System oscillating between conflicting solutions.
     Recommendation: Identify and resolve conflicting constraints.
  ...
  Attempt 20: remove parameter Y -> failure

  Results: 10/20 successful (50.0%)
  Diagnostics triggered: 5

======================================================================
COMPARISON
======================================================================
Naive RSI success rate:    30.0%
SO-RSI success rate:       50.0%
Improvement:               +20.0 percentage points

SO-RSI detected 5 anomalies and ran diagnostics to understand root
causes before attempting fixes.
======================================================================

======================================================================
ANOMALY DETECTION DEMONSTRATION
======================================================================

Processing execution traces...

⚠️  Trace 3: increase learning rate -> failure
   Anomalies: ['recurrence']
   🔍 recurrence_mechanism_probe: Investigate underlying constraint or
   assumption causing the recurrence.

⚠️  Trace 7: decrease learning rate -> failure
   Anomalies: ['opposing']
   🔍 conflicting_constraints_probe: Identify and resolve conflicting
   constraints or objectives.

⚠️  Trace 12: add regularization -> failure
   Anomalies: ['mismatch']
   🔍 assumption_violation_probe: Update assumptions about environment
   or task dynamics.

✅ Demo complete!

Key takeaway: SO-RSI detects structural anomalies (recurrence, opposing
edits, expectation mismatch) and runs diagnostic probes to understand
root causes before applying patches, leading to systematic workflow edits
instead of symptom-only fixes.
```

### Understanding the Code

**Key Components**:

1. **`ExecutionTrace` dataclass**: Represents an execution trace with:
   - `timestamp`: When the action occurred
   - `action`: What was done
   - `code_change`: The specific change
   - `outcome`: Result (success/failure/error)
   - `expected_outcome`: What was expected (for mismatch detection)

2. **`StructuralAnomalyDetector` class**: Detects three anomaly types:
   - `_detect_recurrence()`: Same fix attempted repeatedly
   - `_detect_opposing_edits()`: Undoing previous changes
   - `_detect_mismatch()`: Outcome violates expectations
   - `trigger_diagnostic()`: Launches targeted diagnostic probe

3. **`NaiveRSI` class**: Baseline first-order approach (patches symptoms)

4. **`SORSI` class**: Second-order approach (investigates root causes)

### How to Extend

**To use with real execution traces**:

1. Replace synthetic trace generation with real trace logs
2. Implement sophisticated anomaly detection (AST analysis, pattern mining)
3. Add more diagnostic probes for specific failure modes
4. Connect diagnostic findings to actual workflow modifications

**Example modification**:

```python
# Replace synthetic traces with real execution logs
def load_real_traces(log_path):
    """Load real execution traces from log files"""
    traces = []
    with open(log_path) as f:
        for line in f:
            # Parse log format
            trace = parse_log_line(line)
            traces.append(trace)
    return traces

# Add more sophisticated recurrence detection
def _detect_recurrence_advanced(self, trace):
    """Use AST diff similarity for recurrence detection"""
    if len(self.trace_history) < 3:
        return False
    
    # Compute AST similarity with recent attempts
    current_ast = parse_ast(trace.code_change)
    for past_trace in self.trace_history[-5:]:
        past_ast = parse_ast(past_trace.code_change)
        similarity = ast_similarity(current_ast, past_ast)
        if similarity > 0.9 and past_trace.outcome == "failure":
            return True
    return False
```

---

## Common Issues and Solutions

### Issue: NumPy not installed

**Error**: `ModuleNotFoundError: No module named 'numpy'`

**Solution**:
```bash
pip install numpy
```

### Issue: Python version too old

**Error**: Syntax errors or `TypeError` with f-strings

**Solution**: Ensure Python 3.8 or higher:
```bash
python --version  # Should be 3.8+
```

### Issue: Demo runs but results are random

**Observation**: Results vary between runs

**Explanation**: Demos use random number generation for synthetic data. This is intentional to show variability. For reproducible results, set a seed:

```python
import random
import numpy as np

random.seed(42)
np.random.seed(42)
```

Add these lines at the top of each demo file.

---

## Performance Tips

### For Budget RSI

- Reduce number of edits: Change `generate_synthetic_edits(128)` to `generate_synthetic_edits(64)`
- Reduce test instances: Modify the held-out calculation
- Use smaller feature set: Change `num_features=8` to `num_features=4`

### For SO-RSI

- Reduce trace count: Change range in `compare_approaches()` from 20 to 10
- Simplify anomaly detection: Disable one or more detection methods
- Reduce diagnostic probes: Comment out probe result printing

---

## Next Steps

After running the demos:

1. **Understand the concepts**: Read the full paper summaries in `PAPER_SUMMARIES.md`
2. **Implement on your own task**: Adapt the code to your code editing or debugging workflow
3. **Explore other papers**: Check the partial demos in folders 03-09
4. **Complete the full course**: Follow the updated course map in `../COURSE-MAP.md`

---

## Troubleshooting

### Demo doesn't produce expected improvement

**Cause**: Random variation in synthetic data

**Solution**: Run multiple times or set random seed for reproducibility

### Demo crashes with memory error

**Cause**: Too many edits/traces generated

**Solution**: Reduce dataset size in generation functions

### Output is overwhelming

**Cause**: Too much diagnostic output

**Solution**: Comment out print statements in diagnostic probes

---

## References

- Budget RSI Paper: https://arxiv.org/abs/2610.29121
- SO-RSI Paper: https://arxiv.org/html/2610.05701
- Full Course README: ../README.md
- Paper Summaries: PAPER_SUMMARIES.md

---

**Last updated**: October 26, 2026

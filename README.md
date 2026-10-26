# RSI Masterclass 2026 - October Paper Showcase

**Revamped Version - October 2026 Update**

This masterclass now highlights the latest October 2026 RSI research papers with practical, laptop-executable implementations. The course has been completely redesigned to showcase cutting-edge recursive self-improvement research.

## 🚀 October 2026 Featured Papers

We've integrated 9 cutting-edge October 2026 RSI papers into the curriculum:

### 📚 Core Papers (with laptop-executable examples)

1. **[Recursive Self-Improvement on a Budget: Scoring Code Edits Before They Run](https://arxiv.org/abs/2610.29121)**
   - **Laptop showcase**: Implement a linear readout scorer for code edits
   - **Key insight**: Score proposed edits on a steering split before full evaluation
   - **Benchmarks**: HumanEval+, Polyglot (can use small subsets for laptop)
   - **Demo location**: `12_october_2026_papers/01_budget_rsi/`

2. **[Second-Order Problem Solving for Recursive Self-Improvement (SO-RSI)](https://arxiv.org/html/2610.05701)**
   - **Laptop showcase**: Diagnostic probes for structural anomalies
   - **Key insight**: Investigate WHY failures occur before patching
   - **Benchmarks**: Lean 4 proofs, Verus code (small examples)
   - **Demo location**: `12_october_2026_papers/02_second_order_rsi/`

### 📖 Research Studio Papers (mechanism analysis)

3. **[AReaL-RSI: Adaptive Scaling and Coordination](https://arxiv.org/html/2610.18083)**
   - Persistent research team with leader agents
   - Conditional memory sharing
   - Evidence-based review cycles

4. **[RSIFlow: Adaptive Self-Improvement Workflows](https://arxiv.org/html/2610.21791)**
   - Evolving meta-agent for workflow orchestration
   - Adaptive bottleneck targeting

5. **[RSIGym: A Flexible Environment for RSI](https://arxiv.org/html/2610.10310)**
   - Everything-as-a-Service (EaaS) environment
   - Data, Harness, and Joint improvement tracks
   - RSI-Index metric

6. **[Self-Evolving Coding Agents via Harness-Policy Optimization (Self-HPO)](https://arxiv.org/html/2610.22791)**
   - Alternating harness and policy optimization
   - Policy as its own harness proposer

7. **[Terminal-RSI: Recursive Self-Improving Terminal Agents](https://arxiv.org/html/2610.22192)**
   - Recursive Self-Rewrite (RSR) + Recursive Policy-Refine (RPR)
   - Actor-critic coordination

8. **[R2Orch: Recursive Self-Improvement for Agent Orchestration](https://arxiv.org/html/2610.22740)**
   - Self-play within skill-internalization loop
   - Recursive Learnability objective
   - Skill Withdrawal mechanism

9. **[SwarmRSI: Recursive Self-Improvement through Evolving Scientific Agent Swarm](https://arxiv.org/html/2610.20431)**
   - Feedback-Guided Swarm Mutation
   - Complementary Swarm Recombination
   - Recursive Swarm Evolution

## 🎯 Updated Course Structure

### Part 1: Foundations (Themes 00-06) - *Unchanged*
- Start with one prediction task
- Build dependable workflows
- Learn loops, graphs, and ontologies
- Understand system intelligence
- Build meta-harnesses

### Part 2: The Self-* Family (Themes 07-09) - *Enhanced*
- **Enhanced Theme 07**: Now includes October 2026 paper examples
- **Enhanced Theme 08**: Measuring improvement with new metrics from papers
- **Enhanced Theme 09**: Recursive self-improvement with budget-constrained examples

### Part 3: October 2026 Research Studio (Theme 10) - *Complete Revamp*
The research studio now features 13 groups (38 labs) organized around October 2026 papers:

| Group | Paper Focus | Labs |
|-------|-------------|------|
| **00-02** | Reading Frontier Research (Foundations) | 10.01-10.06 |
| **03-05** | Budget RSI: Scoring Before Running | 10.07-10.15 |
| **06-08** | Second-Order RSI: Diagnostic Inquiry | 10.16-10.23 |
| **09-11** | Scaling RSI: AReaL-RSI & Swarms | 10.24-10.31 |
| **12-13** | Adaptive Workflows: RSIFlow & Self-HPO | 10.32-10.38 |

### Part 4: Capstones (Theme 11) - *Updated*
- **Capstone 1**: Implement Budget RSI on your own task
- **Capstone 2**: Apply SO-RSI diagnostic probes
- **Capstone 3**: Build a simple meta-agent workflow
- **Capstone 4**: Audit an October 2026 paper's claims
- **Capstone 5**: Teaching an October 2026 concept

## 💻 Laptop-Executable Showcase Examples

### Example 1: Budget RSI Scorer (Code Edit Pre-filtering)
```python
# From: Recursive Self-Improvement on a Budget
# Location: 12_october_2026_papers/01_budget_rsi/demo.py

class EditScorer:
    """Score proposed code edits before full evaluation"""
    
    def __init__(self, steering_split_features):
        self.steering_features = steering_split_features
        self.coefficients = None  # Learned from labeled edits
    
    def score_edit(self, parent_solve_rate, diff_features):
        """Predict held-out performance without running"""
        if self.coefficients is None:
            raise ValueError("Train scorer first")
        # Linear readout: w^T * [parent_rate, diff_features]
        features = [parent_solve_rate] + diff_features
        return np.dot(self.coefficients, features)
    
    def train(self, labeled_edits):
        """Learn to score from 96 labeled edits (16-instance fit split)"""
        # Simple linear regression on steering split performance
        X = []
        y = []
        for edit in labeled_edits:
            features = [edit.parent_rate] + edit.diff_features
            X.append(features)
            y.append(edit.steering_solve_count)
        self.coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
```

**Laptop runtime**: < 5 minutes with 100 small code edits
**No GPU required**: Pure NumPy + simple Python parsing

### Example 2: SO-RSI Diagnostic Probes
```python
# From: Second-Order Problem Solving for RSI
# Location: 12_october_2026_papers/02_second_order_rsi/demo.py

class StructuralAnomalyDetector:
    """Detect structural anomalies before patching"""
    
    def __init__(self):
        self.inquiry_memory = []
    
    def monitor_trace(self, execution_trace):
        """Detect: recurrence, opposing edits, expectation mismatch"""
        anomalies = []
        
        # 1. Recurrence: same fix attempted repeatedly
        if self._detect_recurrence(execution_trace):
            anomalies.append("recurrence")
        
        # 2. Opposing edits: undoing previous changes
        if self._detect_opposing_edits(execution_trace):
            anomalies.append("opposing")
        
        # 3. Expectation mismatch: outcome violates expectations
        if self._detect_mismatch(execution_trace):
            anomalies.append("mismatch")
        
        return anomalies
    
    def trigger_diagnostic(self, anomaly_type):
        """Launch targeted diagnostic probe"""
        if anomaly_type == "recurrence":
            return self._probe_recurrence_mechanism()
        elif anomaly_type == "opposing":
            return self._probe_conflicting_constraints()
        elif anomaly_type == "mismatch":
            return self._probe_assumption_violation()
```

**Laptop runtime**: < 2 minutes for 50 execution traces
**No GPU required**: Pure Python trace analysis

## 📊 What's New in October 2026 Version

### New Metrics Introduced
- **RSI-Index**: Mean fraction of remaining performance gap closed (from RSIGym)
- **Steering-split solve rate**: Performance proxy for selection (from Budget RSI)
- **Recursive Learnability**: Task choice quality metric (from R2Orch)

### New Mechanisms Covered
- **Linear readout scoring**: Pre-filter edits before execution
- **Second-order diagnostics**: Investigate root causes before patching
- **Conditional memory sharing**: Distinguish resolved vs unresolved findings
- **Skill withdrawal**: Remove skills when no longer needed
- **Evolving meta-agent**: Adapt workflow orchestration

### New Environments
- **RSIGym**: EaaS-based research environment
- **Self-play loops**: Orchestration through internal competition
- **Swarm recombination**: Share partial results across agents

## 🎓 Learning Path Updates

### Quick Start (5 hours)
- Theme 00-02: One prediction → dependable loops
- **NEW**: Theme 07.5: Budget RSI demo (30 min laptop example)
- Theme 11.1: Budget RSI capstone (2 hours)

### Standard Course (30 hours)
- Themes 00-09: Full foundations
- **NEW**: Theme 10.00-10.05: October 2026 paper reading (3 hours)
- **NEW**: Theme 10.06-10.15: Budget RSI implementation (5 hours)
- **NEW**: Theme 10.16-10.23: SO-RSI diagnostics (4 hours)
- Theme 11.1-11.3: Three capstones (5 hours)

### Full Masterclass (60 hours)
- Complete standard course
- **NEW**: Theme 10.24-10.38: All October 2026 mechanisms (10 hours)
- Theme 11.4-11.5: Audit and teaching capstones (5 hours)
- **NEW**: Theme 12: October 2026 paper deep-dives (10 hours)

## 🔧 Prerequisites

**Updated for October 2026 papers:**
- Basic ML concepts (unchanged)
- Python proficiency (unchanged)
- **NEW**: Familiarity with code editing/diff tools (for Budget RSI)
- **NEW**: Basic understanding of execution traces (for SO-RSI)
- **NEW**: Simple workflow/graph concepts (for RSIFlow)

**Hardware:**
- 8 GB RAM (unchanged)
- CPU-only (unchanged)
- **NEW**: Optional: 100MB disk space for code edit datasets

## 📈 Comparison: Original vs October 2026 Version

| Aspect | Original | October 2026 Update |
|--------|----------|---------------------|
| Papers covered | ~15 papers (pre-Sept 2026) | **9 October 2026 papers** + originals |
| Laptop-executable demos | 0 | **2 full implementations** |
| Research studio groups | 13 groups | **13 reorganized groups** (October 2026 focus) |
| Metrics taught | 5 | **8** (added RSI-Index, steering rate, etc.) |
| Mechanisms covered | 8 | **15** (added SO-RSI, conditional memory, etc.) |
| Environments studied | 3 | **6** (added RSIGym, swarm, self-play) |
| Total labs | 101 | **120** (19 new October 2026 labs) |

## 🚀 Getting Started

### Option 1: Quick October 2026 Preview (1 hour)
```bash
cd rsi/12_october_2026_papers/01_budget_rsi
python demo.py  # Run the budget RSI scorer
```

### Option 2: Full Revamped Course
Follow the standard start, but with October 2026 integration:
```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Start lab 00.01 with me.
Explain the prediction task before running code.
You write the implementation.
I will predict, inspect, and explain.
Wait at the learning checkpoints.
Keep my work in a sibling rsi-work folder.
INCLUDE October 2026 paper examples in Theme 10.
```

### Option 3: October 2026 Paper Deep-Dive (Researcher Track)
Skip directly to Theme 12:
```bash
cd rsi/12_october_2026_papers
# Explore each paper's implementation
```

## 📚 Original Course Retained

The original course materials are preserved in `backup_rsi_original/`. All original labs, illustrations, and evidence remain accessible. The October 2026 update is a **complete revamp** that:
- Reorganizes the research studio around October 2026 papers
- Adds new laptop-executable implementations
- Updates the course map and learning paths
- Preserves all original content for reference

## 🎯 October 2026 Showcase Goal

**Primary objective**: Give students a concrete, laptop-executable understanding of October 2026 RSI advances through:
1. **Budget RSI**: Scoring code edits before running (5-minute demo)
2. **SO-RSI**: Diagnostic probes for root cause analysis (2-minute demo)
3. **Mechanism understanding**: All 9 papers analyzed in research studio
4. **Hands-on capstones**: Implement October 2026 concepts on your own tasks

**Success criteria**: After completing the October 2026 showcase, students can:
- Explain why scoring edits before execution matters
- Run a budget RSI loop on their own code
- Detect structural anomalies in execution traces
- Compare October 2026 RSI approaches to earlier methods
- Audit an October 2026 paper's claims with evidence

## 📖 Documentation

- [Updated Course Map](COURSE-MAP.md) - Full October 2026 integration
- [October 2026 Paper Summaries](12_october_2026_papers/PAPER_SUMMARIES.md) - Detailed analysis
- [Laptop Demo Guide](12_october_2026_papers/LAPTOP_DEMOS.md) - How to run examples
- [Original Course Map](backup_rsi_original/rsi/COURSE-MAP.md) - For reference

## 🔗 Links

- [Original Course](backup_rsi_original/rsi/README.md)
- [October 2026 Papers on arXiv](https://arxiv.org/list/cs.AI/recent)
- [GitHub Repository](https://github.com/dlmastery/simple-coding-harness/tree/main/rsi)

---

**Last updated**: October 26, 2026
**Version**: 2.0 (October 2026 Revamp)
**Status**: Complete revamp with 9 new papers and 2 laptop-executable demos

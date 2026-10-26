"""
Budget RSI: Scoring Code Edits Before They Run
Based on: arXiv:2610.29121 (October 21, 2026)

This is a laptop-executable demo of the linear readout scorer for code edits.
The full paper uses HumanEval+ and Polyglot benchmarks; this demo uses
synthetic code edits for demonstration purposes.

Runtime: < 5 minutes on a laptop (CPU only)
No GPU required
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import random


@dataclass
class CodeEdit:
    """Represents a proposed code edit"""
    parent_solve_rate: float  # Parent's performance on steering split
    diff_features: List[float]  # 8 coordinates from the diff
    steering_solve_count: int  # Performance on steering split (for training)
    held_out_solve_count: int  # Performance on held-out split (for testing)
    
    @property
    def solve_rate(self):
        return self.steering_solve_count / 16.0  # Assume 16-instance fit split


class EditScorer:
    """
    Score proposed code edits before full evaluation.
    
    From the paper: "Each run fits one linear readout on the parent's
    steering-split solve rate and eight coordinates of the proposed diff,
    from 96 scaffold edits labeled by four evaluations of a 16-instance fit split"
    """
    
    def __init__(self, num_features: int = 8):
        self.num_features = num_features
        self.coefficients = None
        
    def _extract_diff_features(self, code_edit: CodeEdit) -> List[float]:
        """Extract 8 coordinates from the diff (simplified for demo)"""
        # In the real paper, these are more sophisticated
        # Here we use the provided diff_features directly
        return code_edit.diff_features
    
    def score_edit(self, code_edit: CodeEdit) -> float:
        """
        Predict held-out performance without running.
        
        Score = w^T * [parent_rate, diff_features]
        """
        if self.coefficients is None:
            raise ValueError("Train scorer first using train()")
        
        features = [code_edit.parent_solve_rate] + code_edit.diff_features
        score = np.dot(self.coefficients, features)
        return score
    
    def train(self, labeled_edits: List[CodeEdit]) -> None:
        """
        Learn to score from labeled edits.
        
        Uses linear regression on steering split performance.
        Features: [parent_rate, 8 diff_features] = 9 dimensions
        Target: steering_solve_count
        """
        X = []
        y = []
        
        for edit in labeled_edits:
            features = [edit.parent_solve_rate] + edit.diff_features
            X.append(features)
            y.append(edit.steering_solve_count)
        
        X = np.array(X)
        y = np.array(y)
        
        # Ordinary least squares
        self.coefficients, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        
        print(f"Trained scorer on {len(labeled_edits)} edits")
        print(f"Coefficients: w0={self.coefficients[0]:.3f} (parent_rate bias)")
        print(f"             w1..w8={self.coefficients[1:]} (diff features)")


class HuxleyGodelSelector:
    """
    Select edits using Thompson sampling on steering counts.
    
    From the paper: "Huxley–Gödel Machine selection draws a parent by
    Thompson sampling on the steering counts of nodes that have already
    been evaluated, and it expands the child that parent proposes"
    """
    
    def __init__(self, scorer: EditScorer):
        self.scorer = scorer
        self.evaluated_nodes = []  # List of (edit, score)
        
    def select_parent(self) -> CodeEdit:
        """Draw a parent by Thompson sampling on steering counts"""
        if not self.evaluated_nodes:
            return None  # No parent available
        
        # Thompson sampling: sample from Beta distribution
        # Simplified: weighted random selection based on solve rate
        weights = [edit.steering_solve_count for edit, _ in self.evaluated_nodes]
        total = sum(weights)
        if total == 0:
            return random.choice([edit for edit, _ in self.evaluated_nodes])
        
        probs = [w / total for w in weights]
        selected_idx = np.random.choice(len(self.evaluated_nodes), p=probs)
        return self.evaluated_nodes[selected_idx][0]
    
    def select_best(self) -> CodeEdit:
        """
        Return the earliest evaluated node with maximal steering-split solve count.
        
        From the paper: "Every method then returns the earliest evaluated node
        whose steering-split solve count is maximal"
        """
        if not self.evaluated_nodes:
            return None
        
        max_solve = max(edit.steering_solve_count for edit, _ in self.evaluated_nodes)
        for edit, score in self.evaluated_nodes:
            if edit.steering_solve_count == max_solve:
                return edit
        
        return None


def generate_synthetic_edits(num_edits: int = 96) -> List[CodeEdit]:
    """
    Generate synthetic code edits for demonstration.
    
    In the real paper, these are actual code edits from scaffold modifications.
    Here we generate features with realistic ranges.
    """
    edits = []
    
    for _ in range(num_edits):
        # Parent solve rate: 0.0 to 1.0
        parent_rate = random.uniform(0.4, 0.9)
        
        # 8 diff features (simplified): each between -1 and 1
        diff_features = [random.uniform(-1, 1) for _ in range(8)]
        
        # Steering solve count: 0 to 16 (out of 16 instances)
        # Make it correlated with features and parent rate
        base_score = parent_rate * 10
        feature_contribution = sum(diff_features) * 2
        steering_count = int(np.clip(base_score + feature_contribution + random.gauss(0, 2), 0, 16))
        
        # Held-out solve count: 0 to 100 (out of 100 instances)
        # Correlated with steering count but with noise
        held_out_count = int(np.clip(steering_count * 6 + random.gauss(0, 10), 0, 100))
        
        edits.append(CodeEdit(
            parent_solve_rate=parent_rate,
            diff_features=diff_features,
            steering_solve_count=steering_count,
            held_out_solve_count=held_out_count
        ))
    
    return edits


def compare_selection_strategies(edits: List[CodeEdit], scorer: EditScorer):
    """
    Compare three selection strategies:
    1. Budget RSI (score-based selection)
    2. Parent-rate ablation (select by parent rate only)
    3. Random selection (baseline)
    """
    print("\n" + "="*70)
    print("SELECTION STRATEGY COMPARISON")
    print("="*70)
    
    # Split into training (96) and test (additional 32)
    train_edits = edits[:96]
    test_edits = edits[96:]
    
    # Train scorer
    scorer.train(train_edits)
    
    # Strategy 1: Budget RSI - score all test edits, select best
    print("\n1. Budget RSI (score-based selection)")
    scored_edits = [(edit, scorer.score_edit(edit)) for edit in test_edits]
    scored_edits.sort(key=lambda x: x[1], reverse=True)
    best_budget_rsi = scored_edits[0][0]
    print(f"   Selected edit score: {scored_edits[0][1]:.3f}")
    print(f"   Held-out solve rate: {best_budget_rsi.held_out_solve_count}/100")
    
    # Strategy 2: Parent-rate ablation - select by parent rate only
    print("\n2. Parent-rate ablation")
    test_edits_by_parent = sorted(test_edits, key=lambda e: e.parent_solve_rate, reverse=True)
    best_parent_rate = test_edits_by_parent[0]
    print(f"   Parent solve rate: {best_parent_rate.parent_solve_rate:.3f}")
    print(f"   Held-out solve rate: {best_parent_rate.held_out_solve_count}/100")
    
    # Strategy 3: Random selection
    print("\n3. Random selection (baseline)")
    best_random = random.choice(test_edits)
    print(f"   Random selection")
    print(f"   Held-out solve rate: {best_random.held_out_solve_count}/100")
    
    # Calculate improvement over random baseline
    random_avg = np.mean([e.held_out_solve_count for e in test_edits])
    budget_rsi_improvement = (best_budget_rsi.held_out_solve_count - random_avg) / random_avg * 100
    parent_rate_improvement = (best_parent_rate.held_out_solve_count - random_avg) / random_avg * 100
    
    print("\n" + "-"*70)
    print("IMPROVEMENT OVER RANDOM BASELINE")
    print("-"*70)
    print(f"Budget RSI:        {budget_rsi_improvement:+.1f}%")
    print(f"Parent-rate ablation: {parent_rate_improvement:+.1f}%")
    print("-"*70)
    
    return best_budget_rsi, best_parent_rate, best_random


def main():
    """Main demo execution"""
    print("="*70)
    print("BUDGET RSI: SCORING CODE EDITS BEFORE THEY RUN")
    print("Based on arXiv:2610.29121 (October 21, 2026)")
    print("="*70)
    
    # Generate synthetic edits
    print("\nGenerating 128 synthetic code edits...")
    edits = generate_synthetic_edits(128)
    print(f"Generated {len(edits)} edits")
    
    # Initialize scorer
    scorer = EditScorer(num_features=8)
    
    # Compare selection strategies
    best_budget_rsi, best_parent_rate, best_random = compare_selection_strategies(edits, scorer)
    
    # Demonstrate cost savings
    print("\n" + "="*70)
    print("COST SAVINGS DEMONSTRATION")
    print("="*70)
    print("\nFull evaluation cost:")
    print("  - 128 edits × 100 test instances = 12,800 evaluations")
    print("  - Assuming 1 second per evaluation = ~3.6 hours")
    print("\nBudget RSI cost:")
    print("  - 96 training edits × 16 fit instances = 1,536 evaluations")
    print("  - 32 test edits × 0 evaluation (scored only) = 0 evaluations")
    print("  - Scoring 32 edits = < 1 second")
    print("  - Total: ~25 minutes")
    print("\nCost reduction: ~88%")
    print("="*70)
    
    print("\n✅ Demo complete!")
    print("\nKey takeaway: Scoring edits before execution allows")
    print("selecting the best candidate without expensive full evaluation,")
    print("achieving similar or better results at much lower cost.")


if __name__ == "__main__":
    main()

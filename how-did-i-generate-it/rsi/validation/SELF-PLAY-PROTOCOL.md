# A small self-play learning experiment

Declared on 20 September 2026 before the first training run. The preceding lesson and source remain in commit `e3428ecfb60a73667b2b6434ba24e8b72ef1d9b6`. The earlier role exchange was an interaction analogy. This experiment adds actual retained parameter updates without changing the training procedure.

## Question and fixed choices

Can one tabular policy, trained by playing both sides of tic-tac-toe, perform differently from its untrained version against a fixed random opponent? The game supplies exact outcomes and makes self-generated experience easy to inspect. Regression and classification remain the course's main task family.

- Board: nine cells, X starts, players alternate, three aligned marks win. Stop at the first win or a full-board draw. Illegal moves fail.
- State: the full board and the current player's mark. Action: one empty cell. No symmetry reduction or neural network.
- Initial action values: zero; ties are chosen uniformly with a seeded generator.
- Training: 3,000 games, both sides use the shared evolving table, seed 17, epsilon 0.2, learning rate 0.2. Each move has an epsilon probability of selecting a random legal action.
- After each game, update each visited state-action value toward its player's terminal return: win +1, draw 0, loss −1. This is a tabular Monte Carlo update, not temporal-difference Q-learning or GRPO. The algorithm and budget remain fixed.
- Freeze and hash the learned table before evaluation. Preserve the untrained table, every training move and update, episode outcomes, and the source hash.
- Evaluation: 500 games per policy, half as X and half as O. The random opponent uses seed 29 + game index, and the greedy policy uses a separate seed 43 + game index for ties. Baseline and trained policy receive the same schedules. Their differing actions can lead to different opponent moves; this is not a claim of identical trajectories.
- Evaluate with exploration disabled and learning disabled. Preserve all 1,000 evaluation games, moves, wins/draws/losses by seat, and before/after table hashes. No tuning after these results.
- Counterexample: the untrained baseline interacts with an opponent but performs no updates. Interaction alone leaves its values unchanged. A proposer–critic conversation without a retained learning update has the same missing ingredient, though it is not the same task.
- Budget: 4,000 games total, CPU only, no language-model or foundation-model training. Record tool time and table size; authoring/inference cost is separate and unknown if unavailable. A command gets a 60-second wall-clock limit.

## Checks and limits

Before the full run, check legal moves, wins and draws, rewards from each player's perspective, frozen evaluation, and small-run repeatability. Tests use separate tiny fixtures; their cost is not counted as part of the declared 4,000-game experiment and must be reported separately.

Publish unfavorable results as well as favorable ones. One training seed, one game, and a random opponent cannot establish broad self-play effectiveness. A gain against random play does not prove optimal play. This is an author execution in the same agent context, not a student assessment or independent replication. It cannot support RSI: the policy changes while the improver remains fixed. No paper headline is reproduced.

Keep runtime artifacts under `rsi/evidence/2026-09-20/self-play/`, with a reader-facing report and a measured plot after the run. Preserve the original evidence if any implementation defect requires a new version.

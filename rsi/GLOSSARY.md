# Terms used in the course

[Course](README.md)

| Term | Meaning here | Example or counterexample |
|---|---|---|
| Task model | A fitted regressor or classifier | The bike-demand linear model |
| Baseline | A simple, declared starting method used for comparison | Predict the training median every hour |
| Mean absolute error (MAE) | Average absolute difference between predictions and outcomes | An error of 10 means ten rentals per hour in this task |
| Balanced accuracy | Mean recall across classes | A majority-only binary classifier scores 0.5 when both classes occur |
| Leakage | Evaluation or outcome information enters a place where the prediction contract forbids it | Using the two counts that sum to the target |
| Hill climbing | Propose a change, evaluate it, and retain eligible improvements | Change a feature group while preserving the evaluator; it can stall or overfit |
| Coding agent | A language model operating with instructions, tools, and state | The agent that generates an experiment |
| Skill | A reusable written procedure read by an agent | Inspect error slices before proposing a change |
| Tool | An executable operation | Fit one recipe and save predictions |
| Harness | Organized instructions, tools, state, checks, and limits around execution | A bounded ML workflow |
| Meta-harness | A procedure that generates a harness from a brief | A task-specific harness builder |
| Process | A sequence or structure of actions | Inspect, split, fit, check, report |
| Loop | Repetition with state and an exit condition | Try at most three candidates |
| Execution graph | Dependencies and routes among actions | Invalid data goes to repair before fitting |
| Ontology | Domain concepts, relations, and constraints | Models use features; target-derived inputs are invalid here |
| Taxonomy | A classification of types | Regression and classification under supervised learning |
| Storage schema | The structure of stored records | Required fields in a candidate record |
| Knowledge graph | Concrete entities and relation facts using a vocabulary | Candidate A uses dataset version B |
| System intelligence | Course term for capability of coordinated components | Not a standard RSI level |
| Self-correction | Revising a current output | Correcting a report without saving a new procedure |
| Reflection | Interpreting experience to propose a lesson | A hypothesis about why a candidate failed |
| Learning | Retained adaptation that can affect later behavior; name the mechanism | Memory, skill edits, and parameter updates differ |
| Self-improvement | Retained system change with demonstrated relevant benefit | A better task skill under a fixed improver |
| Self-organization | Changed arrangement or coordination under system rules | Dynamic work redistribution, possibly without a gain |
| Emergence | A specified collective pattern arising through interactions | Not automatic evidence of intelligence |
| Self-play | Experience from interacting roles or copies | Agreement between roles is not ground truth |
| Self-modification | Editing the system’s instructions or implementation | An edit can help, hurt, or do nothing |
| Solver | The component that performs the task | An agent choosing ML experiments |
| Improver | A procedure that proposes and tests changes to a solver or improver | A skill-editing and comparison procedure |
| Structural recursion | A changed improvement procedure governs later improvement work | An inherited check changes the next round |
| Effective recursive improvement | The inherited change improves the improvement process under a stated comparison | Requires more than a better current solver score |
| Acceleration | Increasing progress rate across generations under defined resource accounting | Not established by two wins or an upward sketch |
| Selection set | Cases used to choose candidates | Repeated feedback makes them development data |
| Final evaluation | Evaluation of a frozen retained choice | Public partitions are not secret from this host agent |
| Ablation | A controlled removal or disabling of a component | Compare with and without memory |
| Transfer | Applying a retained method beyond the setting that selected it | Test a bike-research skill on wine classification |
| GRPO | Group Relative Policy Optimization; a model-training approach using relative rewards within rollout groups | A grouped-reward calculation alone is not a full training implementation |

The self-* terms overlap. They are not one universal ladder. A system can organize itself without learning, learn without improving, or modify itself without recursion. Name what changed and the evidence for its effect.

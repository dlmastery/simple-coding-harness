# What changes, and what does the next attempt inherit?

Author audit for lab 10.37, 21 September 2026. Start here without looking at scores. “Fixed” means fixed within the stated comparison or phase. It does not mean that every component of a project is immutable forever.

| System and primary method | Mutable surface | Fixed boundary | Feedback | What later work inherits |
|---|---|---|---|---|
| [Dream-RSI v1, §§2–3](https://arxiv.org/html/2609.14858v1) | Discovery candidates and executable exploration policy | Discovery model and evaluator | Executed discovery results; replay objective | Saved workspaces support continuations; selected policy returns online |
| [RSIAgent v1, §3](https://arxiv.org/html/2609.15364v1) | Actor memory: procedures, scripts, and lessons | Model weights | Curriculum directs practice; separate verifier inspects outcomes | Later actors receive consolidated memory; final evaluation freezes it |
| [AIDE², §§2.4–2.5](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement) | ML solutions inside a search; researcher code in the outer search | Experimental evaluation protocol | Evaluated solution searches | Discovered researcher runs later searches; ignition tests its use in the outer role |
| [ScientistTwo v1, §§3.1–3.6](https://arxiv.org/html/2609.19644v1) | Hypotheses, implementations, experiments, manuscripts | The inspected iteration does not establish a revised research controller | Experiments, critics, simulated review and rebuttal | Discovered methods become context for later discovery |
| [ScienceBuddy v1, §§2.3–2.5](https://arxiv.org/html/2609.17523v1) | Harness procedures; task-model weights in a later phase | Task model during harness edits; selected harness during RL; auxiliary editor, tools, and evaluators | Researcher-derived tasks, trajectories, rubric rewards | Selected harness and trained checkpoint enter the next cycle after reassessment |
| [MetaRSI v2, §§4.6–5.1](https://arxiv.org/html/2609.06396v2) | Data, harness, accessible weights, operator policies, routing instructions | Verifier, protected release rule, sealed measurement | Execution oracles and retained lineage | Released successor plus accepted operator and routing revisions |
| Local two-generation run, [copied lineage](../../../../rsi/evidence/2026-09-20/two-generations/LINEAGE.md) | Task recipes; two proposed promotion-rule changes | Shared runtime, partitions, external score check | Training and selection MAE under declared rules | Better task recipe; unchanged active improver after both proposals fail |

These rows describe different changed objects. They are not rungs on a universal maturity ladder. The term “RSI” in a source title does not remove the need to inspect that source's own definition.

Now open [results with their protocols](RESULTS-AND-BOUNDARIES.md). Returning here afterward makes it easier to separate an interesting mechanism from evidence that it improves outcomes.

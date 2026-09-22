# An agent changes a search policy

This experiment replaces a flat recipe table with real discovery trees. Each
child inherits its parent's saved code. A fixed program proposes a pipeline
change; the coding agent revises the policy that chooses what to explore next.
The selected policy is then used on new development tasks.

The three generations executed **43 fits**. All succeeded. Independent checks
verify predictions, metrics, parent snapshots, budgets and agreement between
online decisions and replay. This is a controlled laptop adaptation of a
discovery/replay cycle, not a reproduction of Dream-RSI's full agent system.

| Generation | Policy | Classification: fits / selection balanced accuracy | Regression: fits / selection MAE |
|---|---|---|---|
| 0 | Fixed broad exploration | 12 / 0.911774 | 12 / 0.232303 |
| 1 | Promoted revision 2 | 4 / 0.908784 | 2 / 0.242510 |
| 2 | Retained revision 2 | 1 / 0.937299 | 12 / 0.336272 |

Each row uses different task instances. **Do not subtract scores across rows
and call the difference improvement.** The policy reduced actual attempts on
some tasks, but paired controls and final rows are still needed to assess that
tradeoff. On the harder last regression task it used its full allocation and
kept an earlier candidate.

## Follow the evidence

1. Read the [protocol](../../../../how-did-i-generate-it/rsi/validation/ONLINE-DISCOVERY-PROTOCOL.md)
   and [policy-development record](../../../experiments/tabular-discovery/POLICY-DEVELOPMENT.md).
2. Inspect `generation-0`: each node has its inherited manifest, candidate,
   prediction rows, process logs and terminal record.
3. Inspect `replay-0` and [the first promotion](promotion-0/PROMOTION.md).
   Three agent-written revisions compete with the incumbent under one fixed
   quality/cost rule. Revision 2 wins.
4. Inspect `generation-1` and the second replay round. A tighter threshold is
   worse, an unsupported branch is ineligible, and a tied revision loses the
   tie to the incumbent. [The second promotion record](promotion-1/PROMOTION.md)
   retains the existing policy.
5. Inspect `generation-2` for actual use of the retained source. Each rollout's
   `contract.csv` pins its policy and inputs. Each `CHECKS.csv` records the
   independent audit.

The inner proposer is a frozen deterministic program. The policy author is
the current coding-agent session, with shared context. No independent agent
roles, general scientific transfer, recursive acceleration or net total-cost
gain is claimed. Inference cost is unknown. All tasks are synthetic instances
of three declared signal families. No final rows were created in this phase.

## Reproduce and inspect

The agent-operated implementation is [discovery_run.py](../../../tools/discovery_run.py).
Use a fresh sibling workspace. The `task`, `init`, `run`, and `replay` actions
are separate so that source freezes precede execution. The independent checker
is [check_online_discovery.py](../../../../how-did-i-generate-it/rsi/scripts/check_online_discovery.py).
The promotion rule is [select_discovery_policy.py](../../../../how-did-i-generate-it/rsi/scripts/select_discovery_policy.py).
Students should ask their coding agent to perform these operations rather than
write Python or configuration by hand.

The archive contains 670 byte-verified source-workspace files. Its
[manifest](ARCHIVE-MANIFEST.csv) excludes only regenerable Python caches.
Generated Markdown and CSV retain original sibling-workspace paths: a path
beginning `../rsi-work-2026-09-22-discovery/` maps to the same suffix in this
archive. Preserve those original bytes; use the mapping when inspecting a
clone. The README and manifest are publication additions, not run outputs.

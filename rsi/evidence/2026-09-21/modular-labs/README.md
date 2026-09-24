# A local repair can pass while its combination fails

Author walkthrough for labs 10.10–10.12, executed on 21 September 2026. Eleven deterministic interface fixtures ran with **zero model fits**. A separate lineage audit inspected retained evidence without rerunning its experiments.

The two results are distinct: the context-only repair worked on its two cases; the later two-edit combination failed and was rejected. An expected refusal is a useful test result, not a successful harness.

## Find the first missing fact

Both constructed inputs contain candidate `trial-001` and a two-second duration. The short input passed H0. In the long input, observation still contained the candidate, but context compression removed it. Completion then refused to continue. Compare the [short trace](10-10/before-short/TRACE.csv), [long observation](10-10/before-long/OBSERVATION.md), and [long context](10-10/before-long/CONTEXT.md).

After reading those records, the actor wrote a [diagnosis](10-10/DIAGNOSIS.md) and a [context-only patch](10-10/context-patch.py). It removes the long details field while retaining identity. The other source files and fixed driver remain unchanged. The [component hash comparison](10-10/DIFF.csv) records the exact edit.

| Case | H0 | H1, context patch | What the check establishes |
|---|---|---|---|
| Short observation | Accepted | Accepted | The existing passing path still works |
| Long observation | Refused: candidate missing | Accepted | Identity now survives this compression path |

The [long patch check](10-10/after-long/RESULT.md) and [short patch check](10-10/after-short/RESULT.md) both retained the two-second value and reached the stub. The two prerequisite trace captures are charged separately from the two patch checks. No model trained. Details strings and durations are fixture values, not measured ML runtimes.

The [two-component alternative](10-10/TWO-COMPONENT-PROPOSAL.md) stays unexecuted. It explains how shortening observations upstream could mask whether the context patch was necessary. The small fixture does not test whether dropping details preserves all useful information in a real agent.

## Test the combined interface

The next activity declared [four versions and their interfaces](10-11/INTERFACES.md) before any comparison. A compacts duration into `duration_seconds`. B requires an explicit `duration_unit` field. The base completion component accepts either representation, so each edit can work alone. Their combination removes a field that the new completion check requires.

| Execution | Version | Fixture | Actual harness result | Stub reached? |
|---|---|---|---|---|
| 1 | Base | Original: 2 seconds | Accepted; 2 seconds | Yes |
| 2 | A only | Original | Accepted; 2 seconds | Yes |
| 3 | B only | Original | Accepted; 2 seconds | Yes |
| 4 | A+B | Original | Refused: required units field absent | No |
| 5 | Base | Fresh: 0.5 minutes | Accepted; 30 seconds | Yes |
| 6 | A+B | Fresh | Refused: required units field absent | No |
| 7 | A+B | Malformed: candidate missing | Refused: candidate identity missing | No |

The [plan](10-11/PLAN.csv) and [frozen inputs and versions](10-11/FREEZE.csv) preceded these executions. The fresh fixture was not used to select or edit either component, but the author designed it and knew its contents. It is a transfer check within a constructed interface family, not a blind generalization test.

The combination is [rejected](10-11/DONE.md). No repair or extra execution was hidden after that result. The seventh check gives a [specific failure before the stub](10-11/check-07-malformed-AB/RESULT.md). Every expected outcome matched; the three refused combined executions remain failures of the proposed integration.

## Name the procedure on each lineage edge

The [local claim audit](10-12/CLAIM-AUDIT.md) reads the earlier two-generation experiment. Its [eight typed edge rows](10-12/TYPED-EDGES.csv) distinguish six task proposals from two improver proposals. Twenty-eight source files were copied and checked; applied improver hashes agree with the before-action traces.

The task skill improved in generation two, but both proposed improver revisions were rejected. The next round still read the original improver. This run therefore does not demonstrate an accepted revised improvement procedure governing later work. The [copy without improver identity](10-12/WITHOUT-IMPROVER.csv) shows how a result table becomes less informative when the applied version and hash disappear.

The [source mechanism maps](10-12/SOURCE-MAPS.md) separately inspect DGM, HyperAgents, and ModularRSI. The original DGM and HyperAgents figures were viewed in the browser. They are not labels to paste onto a local ancestry chart without checking its versions and actual later use.

## Inspect or reproduce

The [protocol](PROTOCOL.md) predates execution. The [driver](run-modular-labs.py) has preparation, patch, integration, and archive phases. Preparation pauses for the actor's diagnosis and patch; later phases refuse existing outputs. The driver contains fixed orchestration; `loop.py` documents its order rather than implementing an independent scheduler. Observation, context, completion, and the tool stub are loaded from the retained version files.

Use the lab README and tutor skill to create your own separate workspace. Students write intent; their coding agent creates the implementation. Do not run this archive as a fresh experiment or interpret its fit stub as model training.

The [execution ledger](EXECUTIONS.csv) records every fixture outcome, stub count, and measured fixture time. Those times exclude author reasoning, source reading, most process startup, and archive work. Agent inference costs are unknown. The [manifest](MANIFEST.csv) covers 173 original files, verified against the original sibling workspace and this archive. It includes generated bytecode for provenance; do not load archived bytecode as a portable implementation. The manifest and this README are outside that manifest.

This evidence does not establish independent-agent behavior, full paper reproduction, real learner understanding, or general harness transfer. All existing lesson infographics remain unchanged.

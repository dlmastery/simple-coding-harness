# Dream-RSI: history, replay, and new evidence

[Research studio](../README.md) · [Course](../../README.md)

Build a small tree from actual ML attempts. Use that recorded structure to compare replay policies, keeping absent outcomes unknown. Finally, return to fresh work and test whether the replay-selected policy still helps.

![Replay follows a recorded baseline and tried change, while a failed attempt remains archived. It stops before an untried branch whose outcome is unknown. A separate new execution would produce a new report.](../../assets/illustrations/replay-boundary-v2.png)

*The left panel is the record before another run. Replay can reuse its supported outcomes and failure status; it cannot supply D’s missing result. The right panel shows the additional execution needed to extend that record. This is a classroom mechanism inspired by Dream-RSI, not a reproduction of its benchmark or a claim that all counterfactual policies are covered.*

[Open the illustration at full size](../../assets/illustrations/replay-boundary-v2.png).

Find the first branch with no recorded outcome. The replay must stop there. The later live experiment supplies new evidence and has its own cost; it cannot be retroactively included in the earlier record.

**Start with:** Use a new bike workspace, a three-attempt plan, and the task/evaluation boundaries learned earlier. The later online comparison has its own declared budget.

- [10.07 · Build a tree of attempted solutions](step_07_discovery_tree/README.md): A small discovery tree whose nodes link to actual ML trial outcomes.
- [10.08 · Replay only what the history can answer](step_08_replay/README.md): Two replay policies evaluated on a recorded discovery tree, with explicit missing coverage.
- [10.09 · Test the replay winner on fresh work](step_09_online/README.md): An online confirmation comparison after replay selection.

**Carry forward:** Keep separate records for history collection, replay selection, and online confirmation, including their costs. A successful replay does not supply evidence for an unvisited branch.

Read the source connection in each lab. The required path fits a laptop; actual large-model training is an optional, separately planned extension.

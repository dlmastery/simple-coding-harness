# Exploration and memory

[Research studio](../README.md) · [Course](../../README.md)

Start with broad probes of the familiar bike task, then use their errors to choose a focused follow-up. Separate checking a result from writing a lesson about it. Freeze memory when measuring its effect, and keep current run state distinct from reusable experience.

![A curriculum selects practice. The actor executes an experiment, the verifier checks observed evidence, and the actor writes a bounded memory. After exploration, the memory is frozen and read on a later task.](../../assets/illustrations/actor-memory-v2.png)

*The verdict concerns the task outcome. The actor still has to interpret it and can write an overbroad lesson. The notebook fields are our teaching aid, not a required paper format. This figure adapts RSIAgent’s responsibility split to the laptop ML exercise. It does not reproduce the paper’s environments or establish that the memory-writing procedure improved. Frozen evaluation memory is read without updates.*

[Open the illustration at full size](../../assets/illustrations/actor-memory-v2.png).

Trace the verdict to the actor’s pen. Checking an outcome and deciding what to remember are separate actions. Before running, name a lesson that would overgeneralize even from a correct verdict.

**Start with:** Bring the bike task contract, result checker, and memory distinctions from theme 07. The tutor prepares fresh bounded workspaces and identifies any shared-context comparison.

- [10.03 · Choose experiments that reduce uncertainty](step_03_exploration/README.md): A small exploration plan that moves from broad probes to a focused ML question.
- [10.04 · Verify the outcome, then let the actor write memory](step_04_actor_memory/README.md): An outcome check and a separate actor-authored memory update.
- [10.05 · Evaluate with memory frozen](step_05_frozen_memory/README.md): A memory-versus-no-memory comparison with updates disabled during evaluation.
- [10.06 · Separate working state from reusable experience](step_06_working_and_experience/README.md): Two memory stores with different lifetimes and update rules.

**Carry forward:** Keep the exploration plan, outcome verdict, memory comparison, and two-store retrieval checks. Next, give the experiment history a structure that can support replay.

Read the source connection in each lab. The required path fits a laptop; actual large-model training is an optional, separately planned extension.

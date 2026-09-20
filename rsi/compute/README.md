# Take an experiment beyond your laptop

[Course](../README.md) · [Scale skill](../skills/scale-experiment/SKILL.md)

Your laptop teaches the research process. A larger machine changes where the work runs. It does not decide the scientific question for you.

Suppose your research skill proposes a candidate and the evaluator scores its predictions. On a laptop, the candidate finishes before the next proposal. On a cluster, it may wait in a queue, fail on a worker, or finish after a later candidate. The skill still needs an unambiguous answer: which candidate ran, on which data, under which evaluator, at what total cost?

This guide defines that handoff. The supplied CPU runner is tested. GPU, scheduler, and cloud adapters must be generated and tested against your actual environment. No remote backend is bundled as proven support.

## Choose what you are scaling

| Your aim | What changes | What must be explicit |
|---|---|---|
| Run the same experiment elsewhere | Execution backend | Same data, code, split, metric, candidate, and budget |
| Train a larger model | Candidate family and training resources | A new experiment contract; matched resources for comparisons |
| Use a larger dataset | Data and often split design | Provenance, input availability, new baseline, and evaluation scope |
| Run more candidates at once | Search scheduling | Total attempts, concurrency, stale proposals, and stopping rule |
| Update an LLM and its harness | Both parameters and workflow | Training data, reward source, compatibility, independent evaluation, and each update's cost |

Do not copy the small course scores into a claim about a larger system. More compute can improve task results without improving the procedure that selects experiments.

## Prepare one readable brief

Open your agent at the repository root. Give it this prompt:

```text
Read rsi/skills/scale-experiment/SKILL.md and rsi/compute/README.md.
Help me move my completed experiment to the compute I already have.
Read my task contract and results first.
Use rsi/compute/JOB-BRIEF.md to ask for the details that are still missing.
Write the code, environment files, and launch files yourself.
Start with a local check and a tiny backend smoke job.
Show what will run, what it can cost, and how I can stop it.
Do not submit a large job until its scope and budget are authorized.
```

You supply intent and access through your normal secure connection. The agent records connection names and permitted paths, never passwords or tokens. You do not type scheduler syntax or machine configuration.

The agent saves the completed brief, generated adapter, environment versions, and checks in your learner workspace. The [adapter contract](ADAPTER-CONTRACT.md) specifies what those files must do. The [backend checks](BACKEND-CHECKS.md) specify what must actually run before the adapter is called tested.

## Keep one identity through the job

Give each candidate an identity before submission. Give each submission attempt its own identity and retain the parent candidate link. If a scheduler returns a job ID, record it with that attempt. A retry adds cost and a new attempt; it does not become a free first try.

Keep the candidate recipe, training code, data manifest, split, evaluator, and proposing skill versions with the result. Downloading a newer dataset or silently installing different dependencies can invalidate a comparison even when the candidate name is unchanged.

A successful job exit is only an execution result. Promotion requires valid predictions, the frozen evaluation checks, and the declared improvement rule. A failed check stays a failure even when the scheduler says the job completed.

## Plan for interruption

For an iterative trainer, a useful checkpoint includes model parameters, optimizer and learning-rate state, progress, random states, data-order state where needed, and version identifiers. The agent should test that resuming preserves the intended training protocol. Restoring model weights alone can restart the optimizer and change the experiment.

The small scikit-learn fits in this course do not implement mid-fit resumption. An interrupted fit is recorded, then retried as a new charged attempt if the remaining budget allows it. Do not label a fresh fit as a checkpoint resume.

Ask the agent to interrupt a harmless smoke job, confirm that compute has stopped, and resume or retry it using the declared rule. Keep both attempts and their total cost. An incompatible checkpoint must be rejected with an explanation.

## Keep asynchronous search fair

Three jobs submitted together need not finish together. Decide beforehand whether a round waits for all three, has a deadline, or permits new proposals from partial results. Record which evidence each proposal could see at that time.

A fast model should not receive more trials by accident. Compare search procedures with the same declared budget, including failures, queue time where relevant, training, evaluation, proposal inference, and retry costs. Report unfinished jobs at the deadline. Never replace their unknown outcomes with optimistic scores.

## Use a larger model only when it answers a question

For traditional ML, start with a larger permitted tabular problem and a simple baseline. A single-GPU neural network or another supported estimator can be a new candidate family. Keep train-only preprocessing and the evaluator contract. The agent selects and verifies the current training library against your hardware before generating setup.

For ScienceBuddy-style work, a real extension requires an actual model-training implementation and verifiable parameter updates. It also needs training examples, a reward or correction process, and a protocol for evaluating each model with its harness. The numerical exercise in this course supplies intuition. It does not supply a distributed GRPO reproduction.

## What you should receive

The handoff includes a completed brief, a one-prompt entry point, generated setup, a tested small job, cancellation and recovery evidence, a resource ledger, result checks, and known limits. It states the backend and versions that were tested.

You should be able to say, “Run the next candidate within this budget,” or “Stop and save progress,” while the agent handles the infrastructure. Those commands work only to the extent demonstrated by the backend checks.

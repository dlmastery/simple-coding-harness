# Method checks on 20 September

These notes record selected primary-source reading. No paper implementation was reproduced. Full appendices remain outside the completed reading scope.

## HarnessDev

[Version 1, sections 3.2–3.5, 4.1, and 6.1](https://arxiv.org/html/2609.01437v1). Creation and evolution are separate stages. The executor and scorer stay fixed within a comparison; creator and executor can differ. Evolution feedback scores measure adaptation. Later withheld evaluation addresses generalization. The human references are public system results, not uniformly paired controls. One trajectory per creator/runtime cell cannot supply population uncertainty. The study leaves using an evolved harness as the next development environment to future work. Course consequence: lab 10.31 must separate generated-harness quality, builder quality, and inherited improvement machinery.

## Harness-of-Harness

[Version 1, sections 3.1–3.4](https://arxiv.org/html/2609.01481v1). The model, base harness, roles, and runtime policy stay fixed. Software artifacts and execution evidence evolve. Planning, development, and testing use separate invocations; runtime permissions enforce their different authority. Only the developer changes the artifact. Course consequence: repeated project improvement does not establish that the agent harness or its improver changed. Preserve artifact state and evidence state separately. A same-context role prompt in the classroom does not reproduce the source's enforced separation.

## S3Gym

[Version 1, sections 4–5](https://arxiv.org/html/2608.31100v1). Read the method, evaluation separation, and selected results; not every appendix. History, summary memory, and parameter training are different update paths. Self-judging estimates immediate reward under game rules. Ground-truth verifier rewards stay outside exploration feedback in the main setting. Evaluation uses disjoint seeds and is not added to the next update's data. Reported benefits vary; parameter updates can hurt. Course consequence: lab 10.32 is an adjacent external-memory exercise. It omits the games, self-judgment protocol, and actual parameter training. It cannot establish the paper's training effects.

## Additional discovery

[VideoHarness-RSI](https://arxiv.org/abs/2608.24302) first appeared 25 August; version 2 appeared 3 September. Abstract and metadata only. The authors study executable context construction around a frozen vision-language model. This is a useful optional comparison for context-management lessons. Read full methods before making stronger claims.

The date-filtered social search did not verify a new Meta/FAIR post-only result. This is an access and discovery limit, not evidence that none exists. Older results returned by the search engine were not counted as current-month releases.

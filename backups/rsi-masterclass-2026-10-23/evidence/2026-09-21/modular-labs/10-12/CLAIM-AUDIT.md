# What actually changed in the local lineage

The [typed edge table](TYPED-EDGES.csv) has six task-proposal rows and two improver-proposal rows across the fixed and revision-comparison paths. The [identity check](CHECK.md) verified 28 copied source files, the per-arm improver hashes, and the before-action records. This is a read-only audit; it adds no model fits.

## Supported claim

The task skill changed in generation two, while the active improver remained IMPROVER-v0. The original training-MAE rule rejected the generation-one tree and accepted the generation-two weather feature addition. In the comparison path, the proposed selection-based rule tied the active rule in generation one. The proposed 15% training-gain rule lost in generation two. Both improver proposals remained inactive.

The [generation-two active trace](source-records/recursive/generation-2/active/BEFORE.md) names the original rule and its SHA-256 before fitting. The [first decision](source-records/recursive/generation-1/DECISION.csv) and [second decision](source-records/recursive/generation-2/DECISION.csv) both record no improver promotion. The second proposal derives from the retained training-based parent, not the rejected selection-based proposal.

The fixed driver interprets an author-supplied schedule and constructs the prescribed edits. The task/improver files are executable instructions for that constrained interpreter; their presence does not prove autonomous language-model invention. The controller that selects an improver also stays fixed.

## Counterexample to a stronger claim

“The final task error improved over two generations, therefore an improved improver was inherited” is contradicted by these records. The task selection MAE fell from 109.807668 to 99.175924, but the active improver hash stayed unchanged. Proposed, accepted, and later-used versions are different facts.

## Remove the improver identity

[WITHOUT-IMPROVER.csv](WITHOUT-IMPROVER.csv) removes the applied improver path and hash from each edge summary. Task outcomes and source-record links remain. In generation one, equal outcomes hide the different rules tested by the two arms. In generation two, different decisions suggest different behavior, but do not identify the exact applied instruction bytes. Parent/child names elsewhere in the table and the original linked files can recover context; the stripped summary alone is weaker evidence. Do not mistake identical outcomes for identical procedures.

## Missing evidence and next experiment

This local run does not demonstrate a revised improver governing a later generation, much less an effective recursive gain. A useful next experiment would declare a revised improver, test it under matched resources, promote it only if its rule passes the fixed gate, then record its actual use in another comparison. Use fresh conditions and retain rejection if it occurs. No such extra run is authorized by this no-fit lab allocation.

The source mechanism maps are a separate reading exercise. They explain what each historical system permits; they do not change the classification of this local run. No learner or independent-agent assessment occurred.

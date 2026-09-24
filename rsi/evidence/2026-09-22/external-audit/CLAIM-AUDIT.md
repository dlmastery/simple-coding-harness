# A useful recovery result needs an exact acceptance rule

This is a short author audit of [EvoUndo v2](https://arxiv.org/abs/2608.28363v2), followed by an original numerical check. It is not a reproduction. The source trail records precisely which sections and artifacts were inspected.

## Start with the strongest supported interpretation

The paper reports successful recovery repair around fixed forward mutations. Its richer-language/coarse-feedback condition rescues 180 of 197 previously recovery-defective cases. That is useful evidence for the stated recovery problem. It does not show joint optimization of the forward change and its recovery. The paper also reports that effect-scoped snapshots are the stronger baseline in its tested serializable-state setting. [Sections 2.5, 5.2 and 8](https://arxiv.org/pdf/2608.28363v2)

My interpretation is that this belongs in a course about self-modifying systems because undo is a separate property from forward task success. A system can improve the score it cares about while making future repair harder. Students should learn to ask for both forms of evidence. They should not dismiss a recovery result because it fails to prove a stronger claim that was never tested.

At the same time, I would not label a repair loop alone as an inherited improvement to the improver. To make that claim, I would ask for the exact procedure that generates or judges repairs, its revision, and a later run governed by that revision. Those are additional evidence requirements, not a reason to erase a measured recovery result.

## Check what actually decided acceptance

Appendix J.1 corrects an earlier reporting error: the executed rule used separate Wald endpoints; pooled Wilson was post-hoc. The authors report unchanged decisions on recorded candidates, while noting a mathematical disagreement at nineteen successes in each twenty-case group. The richer diagnostic condition is also a bundle, not an isolated address intervention. [Sections 3.3–3.5 and Appendix J.1](https://arxiv.org/pdf/2608.28363v2)

The local calculator enumerated all 441 possible count pairs. At nineteen and nineteen, it obtained 0.854481 for the minimum split endpoint and 0.834958 for the pooled endpoint. At a threshold of 0.85, one rule accepts and the other rejects. Six checks passed. These are our arithmetic outputs, saved in RESULT.md and the CSV tables; they are not outcomes from the authors' experiment.

The charitable statement and the limitation can both be true: two rules may agree on every item in one observed dataset while remaining different rules. A counterexample to universal equivalence does not establish an error in that dataset's reported decisions. Conversely, agreement on a dataset does not justify replacing the original protocol with a different one without disclosure.

## Name the unresolved alternative

My principal uncertainty is artifact-level reproducibility of the acceptance history. A prose correction can be accurate, but another reader still needs enough data to recompute it. A software repository is not automatically that evidence. The [pinned repository](https://github.com/evoundo/evoundo/tree/1d4c96951557f60df9d362e90e4848dad802c40e) presents a product and identifies the paper as its basis. This audit inspected its documentation and tree, not a matched paper-result package or working integration.

The smallest useful follow-up is a read-only reanalysis. Obtain the versioned primary-cohort manifest and per-candidate development status, language validity, two hidden success counts and recorded admission decision. Freeze those files and both formulas. Recompute the original decision and the post-hoc decision for every recorded candidate, preserving rejected and failed cases. Publish mismatch counts, identifiers and hashes. No new language-model sampling is needed for that question.

If the reconstruction matches, confidence in the reporting correction increases. If it differs, investigate version drift, parsing, omitted gates and threshold handling before attributing the difference to the scientific mechanism. A separate future experiment would be needed to test general recovery quality or operational deployment. Our arithmetic check cannot answer those questions.

No model was trained, no source package was installed, and no source-paper result was reproduced. A learner's explanation and an independent peer audit remain unattempted.

# Before the nested researcher comparison

This archive preserves the source and data prepared before the next model
comparison. It does not contain completed training results. The corrected
development run uses exposed tasks; six different datasets remain reserved
for later evaluation under the [declared protocol](corrected-inputs/source/NESTED-RESEARCH-PROTOCOL.md).

The [complete researcher](corrected-inputs/source/researcher.py) owns a feedback
loop with twelve fit slots. Two executable improver versions generate
[child researchers](corrected-inputs/generations/1/i1/GENERATION.md), which must
then run under the same external comparison. Their rewrite space is bounded;
these are not independent LLM agents or weight updates.

## Why the first preflight stopped

The initial I0 rewrite changed the first refinement factor from 0.5 to 1.0.
For an unlimited-depth, leaf-one forest, several larger factors construct the
same model. Replacing the lower factor left only three distinct refinements
in the tested branch, so the loop exhausted its 128-proposal limit before
filling all four remaining fit slots. This happened with synthetic feedback,
before any model training. The [original source](failed-preflight/source/researcher.py)
and [partial checks](failed-preflight/PREFLIGHT-CHECKS.csv) are preserved.
Those checks stop before completion; passing rows alone do not mean the
preflight passed. The failed workspace has no completion marker.

The correction keeps the 0.5 fallback regardless of the inherited first
factor. Its first checker revision also had an incorrect expectation that an
all-failed search must stop after exactly eight or twelve attempts. The
revised researcher can try two alternatives and then stop after ten failures.
That failed checker, its partial trace and its failing verdict are preserved
in [preflight-review-1](corrected-inputs/preflight-review-1/).

The [corrected preflight](corrected-inputs/preflight-source/preflight_nested_research.py)
passes [525 checks](corrected-inputs/PREFLIGHT-CHECKS.csv). It tests four
synthetic incumbent-family scenarios per task and researcher, distinct
constructors, bounds, model selection, earlier parent references, applicability,
failure refusal and the later rejection-recovery rewrite. The fixture scores
are made up to exercise code paths; they are not empirical model results.
Successful completion is now required separately from individual passing rows.

All preparation and preflight work used zero model fits. The corrected
immutable inputs are copied from their freeze manifest. Live worker outputs
were deliberately not copied while being written; their completed execution
archive will follow. [ARCHIVE-MANIFEST.csv](ARCHIVE-MANIFEST.csv) records each
original file's byte count and SHA256. This report and that manifest are extra
publication files. The exception descriptions above are retrospective accounts
of tool output, not original captured stderr logs.

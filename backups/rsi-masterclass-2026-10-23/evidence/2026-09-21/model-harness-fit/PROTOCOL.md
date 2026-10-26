# Model–harness compatibility protocol

Author walkthrough for lab 10.34, 21 September 2026. Save this protocol and the driver before running. Use a new sibling workspace; preserve any existing run.

Freeze a plain-text report contract and its parser before the first check. A report has exactly two nonempty lines: `Candidate: A` and `Status: checked`. Candidate identifiers may be uppercase letters; the allowed status values are `checked` and `unchecked`. Reject missing, repeated, unexpected, or malformed fields. These checks establish structural compatibility only. They do not establish that the candidate was evaluated or that the declared status is true.

Run exactly four parser subprocesses: a valid report; a fluent report with `Result` instead of `Status`; the same report after that one field-name repair; and an incompatible whole-report template. Expected exits are 0, 1, 0, 1. Retain stdout, stderr, each input, elapsed wall time, and before/after parser hashes. Stop on unexpected behavior. No retry, model fit, or weight training is allocated.

Read the primary study's comparison, models, data, and hardware sections. Save a concise source audit with section references, reading date, and a distinction between training and serving hardware. Explain what a real training comparison needs. The local parser experiment is only a compatibility analogy.

Predictions, teach-back, and quizzes are untested with a learner. Inference cost is unknown. Save the complete run and its manifest; update the lab example only from observed results.

# Research and evidence

## Freshness and coverage

Anchor discovery to the date of the run. Search the preceding month and prioritize the latest two weeks. Put explicit start and end dates in every discovery query and use a recency filter where supported. State the dates in the inventory.

Verify publication and revision dates on primary sources. A search filter can fail. A recent crawl, news mention, or social repost does not make old research new. Record the original date and the relevant update separately.

Sweep by mechanism and question, not only by titles already known. Cover major methods, adjacent approaches, failures, evaluations, costs, and limits. Include frontier labs, relevant academic groups, arXiv, official projects, repositories, and original author announcements. Search Google/DeepMind, OpenAI, Anthropic, Meta/FAIR, Microsoft, and other relevant groups without imposing an institutional quota.

Include original X/Twitter threads. Verify account identity and affiliation, canonical post URL, date, the complete relevant thread, and linked evidence. A post can establish what an author announced even before a paper exists. Do not upgrade an announcement into validated performance. Record blocked access and missing sources.

Use third-party summaries for discovery only when technical primary sources are available. Read papers' methods, data, experimental protocol, ablations, limitations, and relevant appendices before teaching their claims. Inspect released artifacts and license terms. Track reading depth so an abstract check cannot masquerade as a full review.

Keep necessary older foundations in a separate, dated list. Honor explicitly requested older works. Stable datasets or standards can be used as references without calling them current research. Do not let historical reading displace the requested current-month sweep.

## Research record

For each included work record:

- Title, authors, affiliations checked, source URL, first date, revision date, and access date.
- Evidence type: preprint, reviewed paper, technical report, lab self-report, theory, post-only announcement, or reproduction.
- Claim and mechanism in plain language.
- What changes, what stays fixed, and where feedback comes from.
- Data, tasks, splits, metric definitions, baseline, resources, and evaluation boundary.
- Main limitations, failed comparisons, uncertainty, and possible confounds.
- Artifact availability, license, what was inspected, and what was actually run.
- The course concept it supports and the simplifications needed for a student exercise.

Store brief source-linked notes rather than unauthorized wholesale copies of papers or websites. Preserve exact queries and a result index. Keep original source artifacts when sharing is permitted; otherwise record a stable identifier, checksum when available, version, and reason the full file is not stored.

## From a paper to a lab

Explain the original problem and the method before adapting it. Define prerequisites just in time. Show a mechanism diagram and map each classroom component to its paper counterpart.

Label the activity accurately:

- **Mechanism exercise:** runs a small version of the idea on a teaching task.
- **Numerical illustration:** exposes a calculation or update without reproducing the original trained system.
- **Simulation:** executes explicit synthetic rules or state changes; its values are not measured behavior of the original system.
- **Replay:** examines recorded outcomes without producing new environment evidence.
- **Result audit:** checks a published claim against its methods and reported results.
- **Source audit:** inspects definitions, mechanisms, dates, or evidence without executing the source system.
- **Reproduction:** executes a sufficiently faithful protocol and reports remaining differences.

Every required lab has a laptop-sized activity. Add GPU or cluster extensions where appropriate. Do not claim model-weight learning from edited prompts or skills. Do not call automated review scores real human acceptance decisions. Distinguish reported results from classroom measurements.

## Evidence rules

Freeze the task, metric, and final evaluation before improvement. Keep development, selection, final test, and transfer roles clear. A file in a candidate-readable folder is not a protected holdout. A fresh role prompt in the same conversation does not erase prior information.

Record whether the author or agent already knew the target-task outcomes. Freezing files before a rerun does not erase that knowledge or establish an uncontaminated transfer test. Report new executions separately from reused prediction tables. A deliberately weak control can explain a mechanism, but must not be presented as typical unaided agent behavior.

Evaluate the retained artifact, not only the best score seen during search. Keep failures, invalid candidates, rejected proposals, and cost. Compare under matched total resources, including proposal generation, evaluation, retries, and failed work. State missing measurements.

Check whether changed instructions were actually used. Use suitable ablations and repeated trials. Avoid claiming a general result from a small illustrative sample. Negative transfer, no improvement, and uncertainty belong in the teaching.

Refresh the research inventory before implementation and delivery. Record additions, corrections, exclusions, and unresolved coverage gaps. A broad sweep is still a bounded search; do not claim exhaustive knowledge of a fast-moving field.

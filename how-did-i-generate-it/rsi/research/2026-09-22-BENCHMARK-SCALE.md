# The gap between a laptop lesson and a research benchmark

Checked on 22 September 2026 while the frozen local comparison runs. This
source review does not change its policies, data or evaluation rule.

The research benchmarks are substantially more demanding than our small
numeric-table examples. They also test different capabilities. A score from
one cannot be interpreted as an RSI score that transfers directly to another.

## Recent benchmark and method sources

[RSI-Exam's maintainer documentation](https://github.com/aiming-lab/RSI-Exam/blob/main/README.md)
dates its website to 26 August and public release to 28 August. It describes
88 tasks in six domains, with 35 public tasks and 53 withheld. Agents receive
up to twelve hours to improve a supplied method. A separate container grades
the submitted artifact on hidden data. These are maintainer-reported design
details, not our reproduction. Its task-level improvement score alone does
not supply the inherited-improver evidence required by this course's stricter
recursive-use distinction.

[Dream-RSI v1](https://arxiv.org/html/2609.14858v1) evaluates algorithm engineering,
mathematical optimization and GPU kernels. Its kernel work must preserve
numerical correctness while improving execution performance. Our fixed tabular
proposer omits that code-generation and hardware-optimization difficulty.
The [official repository](https://github.com/zhengkid/Dream-RSI) still marks the
full implementation and reproduction scripts as forthcoming at this check.

## An older ML benchmark used as a scale reference

[MLE-bench's official documentation](https://github.com/openai/mle-bench/blob/main/README.md)
describes 75 competitions, including a 22-competition low-complexity subset.
Its recommended per-run resources are 24 hours, 36 vCPUs, 440 GB RAM and a
24 GB A10 GPU. It recommends at least three seeds. These are comparison
defaults, not minimum requirements for every task. The full and low-complexity
datasets total about 3.3 TB and 158 GB respectively. Individual tasks vary
greatly; the documented transparent-conductors tabular task is much smaller.
This is an older benchmark consulted directly for implementation context,
not a claimed release from the last month.

## Consequences for the course

Keep the laptop examples for inspecting each mechanism. Their short fits
allow students to examine prediction rows, parent code and failed proposals.
The current policy study tests new instances of a known synthetic grammar.
It supplies neither Kaggle-level modeling evidence nor GPU-kernel evidence.

A stronger transfer stage should select tasks by a declared sampling rule,
use credible baseline procedures, isolate grading data and report resource
use across repeated runs. Choosing a small download does not guarantee an
easy optimization problem. Increasing the budget also cannot repair a
candidate space whose policies all reach the same solutions.

The next real-data extension needs its own protocol. No external benchmark
job, cluster allocation, credential action or task download was performed
for this review.

## Search and reading record

All discovery queries targeted 22 August–22 September 2026:

- `recursive self improvement benchmark machine learning agents MLE after:2026-08-22 before:2026-09-23`
- `Dream-RSI evaluation benchmark tasks compute after:2026-08-22 before:2026-09-23`
- `RSIAgent evaluation benchmark environments limitations after:2026-08-22 before:2026-09-23`

Primary-source domains were used. Search returned some older materials despite
the date operators; they were not classified as new developments. Reading
depth: RSI-Exam setup and evaluation sections, MLE-bench benchmarking and Lite
sections, Dream-RSI experiment/task descriptions and repository release status.
No source result was independently reproduced during this review.

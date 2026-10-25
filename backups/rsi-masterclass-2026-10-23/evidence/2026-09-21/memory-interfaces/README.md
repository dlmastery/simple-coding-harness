# A rejected rule can still teach you something

This walkthrough supports [10.27: separate knowledge stores](../../../10_research_studio/08_skills_and_procedures/step_27_wiki/README.md) and [10.32: compare memory representations](../../../10_research_studio/10_feedback_and_transfer/step_32_memory_interface/README.md). It includes two workflow checks, one separate information-exposure condition, and five author answers checked against exact event arithmetic. No model fitting or weight training occurs.

## Keep the evidence when you reject the rule

The [prior failure](10-27/raw/RESULT.md) comes from the executed meta-skill study. A task proposal silently treats an unknown duration unit as seconds and chooses a candidate when it should refuse the comparison. The [active skill](10-27/ACTIVE-SKILL.md) already has the safer refusal rule.

The new [proposal](10-27/PROPOSAL-NOTE.md) deliberately revisits that known fallback. It passes a seconds-only case but fails the unknown-ticks case. The [gate](10-27/DECISION.md) rejects it and leaves the active skill unchanged. The [notebook](10-27/NOTEBOOK.md) retains the scoped failure lesson, while [its earlier version](10-27/NOTEBOOK-v0.md) and the raw trace remain available.

These stores answer different questions: the trace records what happened, the notebook records a supported interpretation, and the active skill directs the next task. Rejecting one proposed instruction does not require erasing the other two.

The scripted evaluator uses the supplied proposal and case inputs; its [input-identity record](10-27/check-unknown/READS.csv) is not a complete operating-system access log. The [separate exposure condition](10-27/exposure/RESULT.md) actually reads the active skill and notebook together but runs no third task answer. It changes the information interface without measuring a performance effect. The author can read all files throughout.

## Check what a summary preserves

The inventory task has eight events. After event four, the correct checkpoint contains six crates. A deliberately faulty summary omits a removal and says nine. Both receive the same remaining events.

| Supplied representation | Packet words | Author answer | Exact check |
|---|---:|---:|---|
| Raw events | 68 | 8 | Pass |
| Correct summary and tail | 58 | 8 | Pass |
| Faulty summary and tail | 58 | 11 | Fail: original events give 8 |
| Raw events with longer descriptions | 644 | 8 | Pass |
| Correct summary with longer tail descriptions | 346 | 8 | Pass |

Read the [raw packet](10-32/raw/PACKET.md), [faulty packet](10-32/faulty/PACKET.md), [supplied answer](10-32/faulty/ANSWER.md), and [exact check](10-32/faulty/CHECK.md). The checker derives its answer from [the original events](10-32/ORIGINAL-EVENTS.csv). It does not accept the supplied summary as ground truth.

The [expanded-description audit](10-32/PACKET-OPERATION-AUDIT.md) confirms that the state-changing events stayed fixed. Both expanded conditions remained correct in this one exercise. Packet length is measured in characters and whitespace words, not provider tokens. A smaller representation can preserve the answer or preserve an error; length alone cannot tell you which.

The same author designed the sequence, read all five packets, and answered from each representation. The faulty answer demonstrates what the intentionally wrong checkpoint implies. It is not an independently observed agent-memory failure, a clean memory ablation, or evidence of weight learning.

## Inspect the scope and archive

The [interface report](INTERFACE-REPORT.md) records actual information use, shared context, and unsupported claims. The [source audit](SOURCE-AUDIT.md) distinguishes the small exercises from WikiSkill and S3Gym. [Costs](COST.md) retain known action counts and unknown inference costs. Learner assessment, independent contexts, broad memory performance, and larger backends remain untested.

The [manifest](MANIFEST.csv) covers the original workspace files, checked against both original and archive bytes. The manifest and this guide are publication additions outside that list. Preserve this record and start a new sibling workspace for your own attempt.

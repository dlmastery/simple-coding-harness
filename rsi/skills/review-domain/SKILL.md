---
name: review-domain
description: Inspect an RSI course experiment's entities, relations, and invariants using readable Markdown facts and executable checks. Use when a lab asks for an ontology or semantic consistency review.
---

# Review domain meaning

Read the task brief and facts. Identify datasets, columns, targets, transforms, models, partitions, metrics, candidates, and evidence. Define each term by its role in this task. Do not substitute a storage format for the meaning of a fact.

Use a Markdown table with Subject, Relation, and Object columns. Explain one relation in a complete sentence. Distinguish the domain graph from the graph of actions the agent executes.

Run the supplied `audit-domain` tool for its three declared invariants. It checks target-derived features, transforms fit outside training, and selection on final data. It also rejects unknown relation names. Explain that it does not prove the entire experiment valid.

For every failure, quote the relevant fact and rule, show the affected experiment, and propose a correction. Keep the original failing table. Recheck a corrected copy. Ask the learner to predict which records a vocabulary change affects.

If a rule is missing, define it in plain language with a passing example and a failing example. Generate and test an added validator in the learner workspace. Do not silently broaden the meaning of an existing rule.

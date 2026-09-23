# A researcher that another procedure can revise

**Status: development completed; I1's researcher passed the declared gate
with two small gains and four ties. Reserved-task transfer is not yet established.**
Read the [checked development report](../../../evidence/2026-09-22/nested-research-development/README.md).
Sources are frozen before training; read the latest
[implementation record](../../../../how-did-i-generate-it/rsi/IMPLEMENTATION-RECORD.md)
before resuming an existing run.

An ML model answers a prediction question. A researcher decides which models
to try and what to do after a result. An improver changes that research
procedure. The distinction matters: a better model does not prove that the
researcher, or its improver, became better.

Here, each researcher executes twelve model attempts. The first eight cover
different model families. The remaining four depend on its source and observed
feedback. An improver emits a complete executable researcher, including its
search loop and proposal logic. The later generation is built from a retained
parent and actual outcomes of the first generation.

| Object | Source | What can change |
|---|---|---|
| Model | Agent-generated `candidate.py` in each attempt | Template, representation, objective and capacity |
| Researcher | [researcher.py](researcher.py) and generated descendants | How it allocates attempts and chooses parents after feedback |
| Simple improver I0 | [i0.py](i0.py), implemented in [improver.py](improver.py) | Inherited local-refinement multiplier |
| Revised improver I1 | [i1.py](i1.py), implemented in the same module | Coverage, unused alternatives, two-family refinement and rejection recovery |
| Evaluator | Preserved single-fit worker and independent checker | Fixed across the comparison |

These are bounded programs authored by the coding agent. The source rewrite
space is limited. They are not separate LLM agents, do not update model weights,
and do not reproduce a frontier-lab system at its original scale.

## Run through the coding agent

The [execution protocol](../../../../how-did-i-generate-it/rsi/validation/NESTED-RESEARCH-PROTOCOL.md)
declares the tasks, controls, source inheritance, promotion rule and full
624-attempt maximum. It includes all development searches and scoring refits.
It is an author verification study, not the default budget for every student.
The course's smaller [recursive capstone](../../../11_capstones/README.md)
remains the classroom entry point.

```text
Read the nested research protocol and implementation record.
Inspect the existing workspace and live process before acting.
If development search is still running, resume its recorded handle.
After it completes, independently check the entire search before scoring.
Keep every proposal, rejected constructor, failed fit, prediction and source.
Do not retry a spent attempt or tune from the reserved final results.
Explain which object changed and whether its later use is actually measured.
```

The agent uses `run_nested_research.py` for preparation, search and scoring;
`preflight_nested_research.py` for labelled synthetic control-flow checks;
`check_nested_research.py` for trace and prediction verification; and
`revise_nested_research.py` for the fixed outer gate and later source generation.
These scripts are in the repository's authoring directory. The agent writes
and runs implementation code; learners do not type Python or JSON.

## Read the results in the right order

First check that the changed researcher actually chose different experiments.
Then compare its selected model on evaluation rows. Finally compare the
researchers produced by I0 and I1, including all of their development costs.
Fixed and random search remain controls. A rejected proposal, a tie, a quality
gain and fewer fits are different outcomes.

The earlier [six-procedure comparison](../../../evidence/2026-09-22/tabular-comparison/README.md)
is closed and remains visible. The next six datasets have
[checked source rows and grouping](../../../evidence/2026-09-22/nested-data/README.md).
The first preflight also remains preserved: it exposed a duplicate-constructor
exhaustion bug before fitting. Corrected source retains a usable fallback
schedule. Passing that check establishes executable control flow, not RSI gain.

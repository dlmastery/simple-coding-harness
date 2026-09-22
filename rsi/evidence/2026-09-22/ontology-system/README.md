# Name the object, the rule and the evidence

This author walkthrough supplements ontology labs 04.01, 04.02 and 04.05, executes the remaining unknown-relation case for 04.03, and supplies the fixed-system diagnostic for 05.01. Five child commands, six rule fixtures and ten invariants complete with their expected outcomes. **No new model fits or final evaluation run.**

| Activity | Inspect the evidence |
|---|---|
| 04.01: classify ten objects | [Artifact-grounded vocabulary](04-01/VOCABULARY.md), referencing the [fixed-process baseline](../fixed-process/01-02/TRACE.md) |
| 04.01: make improvement claims precise | [Three rewrites and a fully specified measurement](04-01/CLAIMS.md) |
| 04.02: write and explain domain facts | [Five-fact table](04-02/DOMAIN.md), [plain-language explanations and editable side-by-side drawing](04-02/EXPLANATIONS.md), [actual pass](04-02/valid-CHECK.md) |
| 04.02: understand checker coverage | [Omitted-derivation copy](04-02/OMITTED-DERIVATION.md) and its [limited pass](04-02/omitted-CHECK.md); missing facts are not inferred |
| 04.03: reject unknown relation names | [Input](04-02/UNKNOWN.md), [refusal](04-02/unknown-CHECK.md), [command with exit 1](domain-unknown-command.txt); earlier [six base cases and two units cases](../../2026-09-21/foundation-gaps/README.md#invariant-checks-0403) remain separate |
| 04.05: change the prediction-time definition | Versions [one](04-05/VOCABULARY-v1.md) and [two](04-05/VOCABULARY-v2.md), [change record](04-05/CHANGE.md), [impact analysis](04-05/IMPACT.md), [three executed synthetic availability cases](04-05/AVAILABILITY.csv) |
| 04.05: transfer the reasoning to wine | [Binary-to-ordinal task plan](04-05/WINE-ORDINAL.md); no ordinal training or invented score |
| 05.01: give fixed components distinct jobs | [Responsibilities and evidence](05-01/SYSTEM.md), [historical one-fit command](../../2026-09-20/clean-journey/05-01/EXECUTION.md), [original refusal](../../2026-09-20/clean-journey/05-01/LEAKAGE-REFUSAL.md), [current prediction recheck](05-01/PREDICTION-CHECK.md) |
| 05.01: remove the domain guard | [Three dry-run outcomes](05-01/DIAGNOSTIC.csv): guarded refusal, unguarded stub reached, and refusal by a separate teaching allowlist |

“MAE” is a calculation rule. “159.94791188618632 rentals per hour” is one measurement for the named baseline candidate and selection partition. “The model improved” can refer to a task result, a procedure edit or an LLM parameter change; those need different evidence.

The valid domain table passes. An unknown relation is refused. The leaked table fails three rules. Removing its derivation fact from an isolated copy makes that incomplete copy pass. The checker tests supplied facts; it cannot discover what the author left out or prove that an implementation followed them.

The release-time examples admit a forecast known before the origin, refuse tomorrow's observation and refuse an unknown release time. All three timestamps are synthetic. The pinned bike source still lacks the real forecast archive, so the activity produces no forecast performance claim.

The system audit checks a historical one-fit result without training again. Its original controller printed the checked outcome but did not save a separate CHECK.md; the new verdict is saved here with its own command. Removing the domain guard reaches only a dry-run stub. An additional teaching allowlist can block the unfamiliar column, but it does not replace the domain check's meaning rules.

[Protocol](PROTOCOL.md), [source identities](INPUT-IDENTITIES.csv), [ten checks](CHECKS.csv), [32-file manifest](MANIFEST.csv) and [review](REVIEW.md) preserve the boundaries. Child-command wall time totals about 7.432 seconds; fixture timing was not separated, and provider/author costs are unknown. Existing conceptual illustrations were visually reviewed and preserved. The new Mermaid source still needs its rendered appearance checked. Learner responses, independent agents and the proposed new forecasting/ordinal experiments remain unattempted. This navigation page was added after sealing the original files.

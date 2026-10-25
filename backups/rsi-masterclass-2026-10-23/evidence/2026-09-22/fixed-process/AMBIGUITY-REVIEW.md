# Replace “use the best data” with a decision rule

BASELINE-SKILL.md is the version that actually ran. AMBIGUOUS-SKILL.md adds “Use the best data.” It is a teaching copy and was not executed.

One reading is “choose every column that predicts the target well.” That invites casual and registered counts, which sum to the target and leak the answer. Another reading is “use only quality-checked information available for the intended prediction.” The phrase supplies no rule for choosing between them; the rest of the skill prohibits leakage, but adding a conflicting vague instruction creates needless ambiguity.

REPAIRED-SKILL.md replaces the phrase with an explicit rule: use the pinned hourly source and permitted calendar fields for this one-fit baseline; exclude the target, component counts, identifier and raw date. Do not use later observations as advance forecasts. A changed prediction-time setting requires a separate task brief.

No extra fit follows this text edit. The repaired copy is clearer by inspection but has no new execution evidence. Saving an instruction, following it, and establishing its effects are different claims. Learner answers remain unattempted.

Correct this data-science illustration while preserving its crafted drawing, five-scene layout, type, white background, colors, and all unaffected elements.

The partition routes are wrong and MUST be redrawn. Remove both long bottom connector lines entirely, including the blue Train-to-comparison route and the amber Selection-to-fitted-model route. Replace them with:
- A blue arrow from the Train section / "Used to fit the model" to the stack explicitly labelled "Training rows (from Train)" in scene 4. Only Train enters fitting.
- A separate amber arrow from Selection / "Used to check the result" to a clearly labelled bracket "Selection rows" above BOTH the Predictions and Observed targets sheets in scene 5. This carries held-out row identities and targets for checking, not for fitting. This arrow must not touch Training median or Fitted model.
- Preserve Training rows -> Training median -> Fitted model -> Predictions.
- Preserve Predictions -> Compare and Observed targets -> Compare -> MAE + evidence.
- Final stays reserved and has no connector to any fitting or checking action.
Use whitespace lanes and unmistakable endpoints. No lines may end at the wrong object.

Correct the data dictionary to exactly four rows:
"hr" | "hour of day"
"temp" | "normalized temperature"
"hum" | "normalized humidity"
"cnt" | "hourly rentals"
Remove the old fabricated field names and Celsius unit. In the data preview use the column headers "hr", "temp", "hum", "cnt", "…", with only neutral row marks, no numbers.
Change "Observed weather (past values)" to "Observed weather (retrospective)".
Clean the garbled small heading inside the observed-target sheet to "Targets".
Do not add empirical values, plots, claims of secret data, or a feedback loop. Keep the visual quality intact.

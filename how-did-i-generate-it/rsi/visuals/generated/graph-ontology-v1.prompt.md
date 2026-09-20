# Workflow and ontology · prompt v1

Built-in image-generation tool, 20 September 2026. No reference image. User-approved alternative; the tool does not expose model identity.

```text
Use case: scientific-educational.
Create an original professional textbook infographic on a pure white background, landscape 3:2. Elegant dark navy serif title; crisp, large sans-serif labels. Fine illustrated paper objects with restrained shading, clear arrows and generous space. Blue denotes workflow, teal denotes meaning, brick red denotes an invalid path. Dense enough to reward reading, but essential labels legible at 800 pixels wide. No robots, logos, watermarks, fake scores, plots or decorative equations.
Title exactly: "Two graphs, two different questions"
Two equal panels with a strong visual separation. Do not connect the panels with process arrows.

LEFT title: "What runs next?"
Small subtitle: "Workflow"
Show a vertical dependency sequence with solid blue arrows:
"Inspect data" → "Validate split" → a diamond "Valid?"
The diamond has a blue "Yes" branch to "Fit model" → "Check result".
It has a red "No" branch to a separate "Stop and repair" card. No edge from the repair card to Fit model.
Use small distinctive icons: data sheet, partitioned cards, model box, magnifying glass over a report. No measured numbers or graphs. Each solid arrow means the next action depends on the prior result. Keep the failure path completely separate.

RIGHT title: "What does it mean?"
Small subtitle: "Domain facts"
Show five large concept cards arranged as a network, not a vertical schedule:
"Scaler", "Training partition", "Search", "Selection partition", "MAE".
Add a sixth concept card "Model".
Use exactly these THREE teal dashed directed relations, with readable words on the connectors:
Scaler → Training partition, labelled "fit on".
Search → Selection partition, labelled "selects on".
Model → MAE, labelled "measured by".
These three relations can occupy three balanced rows with cards at either end, distinct from the left's connected action sequence. The relation is read as a sentence; do not add temporal arrows between the three rows.
Below the relations, one small outlined note: "Rule: fit preprocessing on training data only."
No invented score or unit ambiguity. MAE is the metric definition, not a generated result.

Bottom legend: solid blue arrow "Dependency"; dashed teal arrow "Meaning".
Bottom takeaway exactly: "A valid schedule can still use the wrong facts."
The instant intuition: workflow edges organize actions; ontology relations express selected meanings and rules. Neither diagram alone proves an experiment scientifically sound. Render only the specified short labels and note; no filler text.
```

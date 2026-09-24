# Target leakage · prompt v1

Submitted to the built-in image-generation tool on 20 September 2026. User-approved alternative to the original Imagen preference. No input image. Returned model identity is not exposed by this tool.

```text
Use case: scientific-educational.
Create an original, polished textbook infographic for an advanced ML codelab that begins with the basics. Pure white background, landscape 3:2, restrained illustrated objects, fine navy outlines, elegant dark navy title, very clear large labels. Use muted blue for allowed inputs, amber for the model, teal for a checked comparison, brick red for a forbidden shortcut. Professional editorial illustration with a small artful bike-station vignette, not flat clip art. Rich but carefully spaced detail. Match a clean illustrated research textbook, no robots, gradients, decorative code, logos, or watermarks.

Title, exactly: "The answer hidden in an input"
Subtitle, exactly: "Retrospective teaching task"
Teach target leakage in the UCI bike-rental task. The target is total rentals in the same hour. Observed weather is permitted here; do not depict or claim a day-ahead forecast.

Main composition: two clearly separated horizontal lanes that meet at the right.
TOP LANE "Inputs": two large blue cards "Calendar" and "Observed weather" feed a box "Allowed features", then an amber small "Model" object, then a blue sheet "Prediction". Only these two inputs enter the allowed route.
BOTTOM LANE "Outcomes": show two red-outlined count tiles "casual" and "registered", with a plus sign, an equals sign, and the tile "total rentals". These are labels only: no made-up numbers, bars, data values, example rows, or scores. Show the addition as "casual + registered = total rentals". The "total rentals" tile connects rightward to a sheet "Observation".
AT RIGHT: the Prediction and Observation sheets both feed a teal magnifying-glass comparison labelled "Check the error". Both inputs to this comparison must be visible and distinct.
FORBIDDEN SHORTCUT: draw a red dashed arrow FROM the pair of component-count tiles UP TOWARD Allowed features. Interrupt this arrow with a clear cross and label "Blocked: reveals the target". The dashed red arrow must not look like an allowed input path. Keep it away from the valid arrows.
Below the outcomes lane, short note exactly: "Keep component counts out of the features."
The whole illustration must make it instantly clear that casual and registered already determine total rentals, so a model that sees them can cheat. Training and evaluation need the target, but the target and its component counts do not enter the model's input features. Do not imply that all outcomes are unavailable to the evaluator. No empirical accuracy claim. All essential labels readable at 800 pixels wide. Generous white space, no paragraphs inside the image.
```

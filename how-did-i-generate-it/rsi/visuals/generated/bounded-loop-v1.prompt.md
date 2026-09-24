# Bounded loop · prompt v1

Submitted to the built-in image-generation tool on 20 September 2026. No input image. Conceptual procedure, with failure accounting and saved-state resumption.

```text
Use case: scientific-educational.
Create a polished, original illustrated textbook infographic on a pure white background, landscape 3:2. Dark navy serif title, clean large sans-serif labels, fine consistent outlines, restrained blue, amber and teal, brick red for failed or stopped paths. Detailed paper notebook, model object, report and clock illustrations, no robots, decorative code, logos, fake graphs, or watermarks. Visually rich but spacious, essential labels readable at 800 pixels wide.
Title exactly: "A loop needs memory and a way out"
Subtitle exactly: "Repeating a command is not enough"

Show a bounded experiment loop with a visible exit and persistent state. Use a clockwise route of four large numbered cards around a central open notebook:
upper left "1 Propose" with small text "Choose one change";
upper right "2 Run" with small text "Reserve an attempt, then fit";
lower right "3 Check" with small text "Verify the result";
lower left "4 Record" with small text "Keep success and failure".
Blue arrows from Propose to Run, Run to Check, Check to Record.
Between Record and the next Propose place a clearly visible diamond "Continue?" on the left edge. Arrow from Record into Continue. From Continue a blue arrow labelled "Within limits" goes to Propose; a red arrow labelled "Limit reached" goes OUT of the loop to a distinct "STOP" card. Do not draw a direct arrow bypassing Continue.
Central open notebook labelled "Persistent state". Four readable entries only: "Candidate identity", "Current best", "Attempts left", "Last checked step". Fine dotted connectors labelled "Read / save" link the notebook to the workflow; these are state connections, not scheduling arrows.
A distinct red dashed arrow from Run directly to Record is labelled "Fit failed". It bypasses Check because a failed fit has no successful prediction report. Near it, exact short note: "The attempt still counts."
A separate small bottom strip shows a paused process icon, then a new process icon reading the SAME notebook, then a small "Continue?" diamond. Label this strip "Resume: read saved state before another attempt". Resume must not reset the notebook or budget.
Bottom note exactly: "A checked result can be worse."
No invented metric values or empirical performance curves. No infinite-loop symbol. Make the persistent notebook, budget gate and stopped path more prominent than the loop arrows.
```

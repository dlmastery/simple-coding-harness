# Native PowerPoint review

Microsoft PowerPoint 16.0 opened the current 37-slide review deck read-only and
without a visible presentation window. The automation exported all 37 slides
and read every slide's notes through PowerPoint's own object model. Complete
notes match the authored text after whitespace normalization on all 37 slides.

The application recognizes native tables on slides 19, 21 and 33, and the native
chart on slide 32. The chart series reads 192, 192, 192, 55, 84, matching the
archived search-attempt totals. The input deck's SHA-256 remains
b7557350d9b49d4d74fe2981bdf9dae0e53af9e25d8825b34b601cd0ec2cc0a1.

## Evidence

- [Executed inspection script](check-native-powerpoint.ps1).
- [Command output](native-v2-command.txt).
- [Application and object results](native-v2/APPLICATION.txt).
- [Per-slide checks](native-v2/NATIVE-CHECKS.csv).
- [Unchanged input check](native-v2/UNCHANGED.txt).
- [All native exports and extracted notes](native-v2/).

The command used Windows PowerShell in STA mode, the current v2 PPTX, its
build-v2/SLIDE-CONTENT.json source and the new native-v2 output directory.
No existing PowerPoint process was present. The script refused that condition
before opening, used a hidden read-only presentation, closed only its own deck,
and exited the application when no other presentation was open. No save,
slide edit, chart-workbook activation or model training occurred.

## Visual inspection

The earlier artifact-tool review inspected every final slide. This independent
native-render review inspected slides 1, 17, 19, 21, 22, 32, 33 and 35 at
1280 × 720. These cover the opening, corrected recursion diagram, all native
tables and the chart, dense research map and capstone map. The inspected native
renders preserve complete figures, readable labels, table rows, signs and
chart values, with no clipping or overlap. The remaining native PNGs are
retained, but no separate visual inspection of every native export is claimed.

This verifies opening, rendering, notes access and native object recognition
on this installed PowerPoint version. It does not certify every Office version,
Google Slides import, slideshow controls, presenter display or classroom pacing.
The deck's mixed empirical findings and review-draft status are unchanged.

## API references

The script follows Microsoft's [Presentations.Open](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open)
parameters for read-only hidden opening, [Slide.Export](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export)
for PNG output and [Slide.NotesPage](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.notespage)
for notes access. These are implementation references, not recent RSI research.

"""Export every slide of the deck to PNG through PowerPoint (COM), for visual QA.

    python genui/slides/render.py [--pdf]    # -> genui/slides/render/Slide1.PNG ... (and the PDF next to the deck)
"""
import os
import sys

import win32com.client

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
src = os.path.abspath(args[0] if args else os.path.join(HERE, "..", "generative_ui_zero_to_hero.pptx"))
out = os.path.join(HERE, "render")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))
try:
    app = win32com.client.GetActiveObject("PowerPoint.Application")  # a running instance (start POWERPNT.EXE /automation first if Dispatch fails)
except Exception:  # noqa: BLE001
    app = win32com.client.Dispatch("PowerPoint.Application")
want_pdf = "--pdf" in sys.argv
pres = app.Presentations.Open(src, WithWindow=False)
pres.Export(out, "PNG", 1600, 900)
count = pres.Slides.Count
pres.Close()
print(f"{count} slides -> {out}")
if want_pdf:  # a PDF built from the renders (PowerPoint's own PDF export is not reachable from a windowless COM session)
    import img2pdf

    pages = sorted(os.listdir(out), key=lambda f: int("".join(ch for ch in f if ch.isdigit())))
    pdf = os.path.splitext(src)[0] + ".pdf"
    with open(pdf, "wb") as f:
        f.write(img2pdf.convert([os.path.join(out, page) for page in pages], layout_fun=img2pdf.get_layout_fun((img2pdf.in_to_pt(13.333), img2pdf.in_to_pt(7.5)))))
    print(f"pdf: {len(pages)} pages -> {pdf}")

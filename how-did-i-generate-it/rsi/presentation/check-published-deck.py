"""Read-only package checks against the authored notes and frozen result CSVs."""
import csv
import hashlib
import json
import posixpath
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BUILD = HERE / 'build-v2'
DECK = HERE / 'output/rsi-masterclass-review-v2.pptx'
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
specs = json.loads((BUILD / 'SLIDE-CONTENT.json').read_text(encoding='utf-8'))
checks = []

def check(name, passed):
    checks.append({'check': name, 'passed': bool(passed)})

def normalized(value):
    return re.sub(r'\s+', '', value)

with ZipFile(DECK) as archive:
    slide_names = [n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]
    check('37 slides', len(slide_names) == len(specs) == 37)
    for spec in specs:
        number = spec['number']
        rels = ET.fromstring(archive.read(f'ppt/slides/_rels/slide{number}.xml.rels'))
        targets = [r.attrib['Target'] for r in rels if r.attrib['Type'].endswith('/notesSlide')]
        check(f'slide {number}: one notes relationship', len(targets) == 1)
        if len(targets) != 1:
            continue
        target = posixpath.normpath(posixpath.join('ppt/slides', targets[0])).lstrip('/')
        notes = ET.fromstring(archive.read(target))
        content = ''.join(t.text or '' for t in notes.findall('.//a:t', NS))
        check(f'slide {number}: complete authored notes retained', normalized(spec['notes']) in normalized(content))
        check(f'slide {number}: source URL in notes', 'https://github.com/dlmastery/simple-coding-harness/' in content)
    chart_names = [n for n in archive.namelist() if '/charts/' in n and n.endswith('.xml') and '/_rels/' not in n]
    check('one native chart', len(chart_names) == 1)
    chart = ET.fromstring(archive.read(chart_names[0]))
    actual = [float(v.text) for v in chart.findall('.//c:ser/c:val//c:pt/c:v', NS)]
    with (REPO / 'rsi/evidence/2026-09-22/discovery-final/RESULTS.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    expected = [sum(int(r['attempts']) for r in rows if r['arm'] == arm)
                for arm in ['broad', 'greedy', 'lineage', 'evolved', 'broad-stop']]
    check('chart values match frozen attempt ledger', actual == expected)
    check('editable chart workbook present', any(n.startswith('ppt/embeddings/') and n.endswith('.xlsx') for n in archive.namelist()))
    result_slide = ET.fromstring(archive.read('ppt/slides/slide33.xml'))
    cells = [''.join(t.text or '' for t in cell.findall('.//a:t', NS)) for cell in result_slide.findall('.//a:tc', NS)]
    with (REPO / 'rsi/evidence/2026-09-22/nested-research-evaluation/CONTRASTS.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            mean = f"{float(row['mean_loss_change']):+.6f}"
            interval = f"[{float(row['interval_low']):+.6f}, {float(row['interval_high']):+.6f}]"
            check(f"{row['parent']}: result table matches frozen contrast", mean in cells and interval in cells)

changed = []
for number in range(1, 38):
    stem = f'renders/slide-{number:02}.png'
    if (HERE / 'build-v1' / stem).read_bytes() != (BUILD / stem).read_bytes():
        changed.append(number)
check('only corrected slide 17 changed visually', changed == [17])
report = {'deck': DECK.name, 'sha256': hashlib.sha256(DECK.read_bytes()).hexdigest(),
          'checks': checks, 'failures': sum(not c['passed'] for c in checks),
          'boundary': 'OOXML and archived-data checks; no native PowerPoint execution.'}
(BUILD / 'CONTENT-CHECKS.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(f"{len(checks)} checks; {report['failures']} failures")
raise SystemExit(bool(report['failures']))

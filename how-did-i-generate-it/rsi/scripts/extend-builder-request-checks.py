"""Execute only the three no-fit checks declared in the request-state addendum."""
import importlib.util
from pathlib import Path
import shutil

source = Path('how-did-i-generate-it/rsi/scripts/run-builder-reconciliation.py').resolve()
spec = importlib.util.spec_from_file_location('builder_walkthrough', source)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
out = driver.OUT
driver.require((out / 'PROGRESS.md').exists(), 'Original stage must finish first')
driver.require(not (out / 'REQUEST-STATE-STARTED.txt').exists(), 'Extension already started')
driver.save(out / 'REQUEST-STATE-STARTED.txt', driver.datetime.now(driver.timezone.utc).isoformat() + '\n')
shutil.copyfile(Path(__file__), out / Path(__file__).name)
check = out / 'package/check-request-state.py'
shutil.copyfile(driver.REPO / 'how-did-i-generate-it/rsi/scripts/check-harness-request-state.py', check)
ledger = out / '06-04-run/trials.csv'
before = driver.digest(ledger)
for candidate, claim, expected in [('trial-001', 'MATCHING-CLAIM.md', 0), ('trial-002', 'UNRELATED-CLAIM.md', 2), ('trial-003', 'UNRELATED-CLAIM.md', 2)]:
    driver.command('state-' + candidate, check, ['--workspace', out / '06-04-run', '--candidate', candidate, '--claim', out / claim, '--output', out / ('STATE-' + candidate + '.md')], expected)
driver.require(driver.digest(ledger) == before, 'Ledger changed')
driver.save(out / 'REQUEST-STATE-RESULT.md', '# Three additional request-state checks\n\nCurrent trial-001 passes. Failed trial-002 and unadmitted trial-003 reject the actual old-success claim. Ledger SHA256 remains ' + before + '. Zero extra fits or admissions; the first nine command results are unchanged.\n')
print('Three request-state checks passed expected outcomes; ledger unchanged; zero fits.')

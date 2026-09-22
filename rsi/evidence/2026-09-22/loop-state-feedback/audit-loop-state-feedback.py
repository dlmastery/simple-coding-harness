"""Read-only analyses of recorded fits and refusals; no model fitting."""
import csv
import hashlib
from pathlib import Path
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO=Path.cwd().resolve()
OUT=REPO.parent/'rsi-work-2026-09-22-loop-state-feedback'
OLD=REPO/'rsi/evidence/2026-09-20/clean-journey'
shutil.copyfile(Path(__file__),OUT/'audit-loop-state-feedback.py')


def rows(path):
    with path.open(encoding='utf-8',newline='') as handle:
        return list(csv.DictReader(handle))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path,records):
    with path.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


pairs=[('Model change',OLD/'02-01/trial-001/error-by-hour.csv',OLD/'02-01/trial-002/error-by-hour.csv'),
       ('Feature change',OUT/'02-03/trial-001/error-by-hour.csv',OUT/'02-03/trial-002/error-by-hour.csv')]
changes=[]
for label,before_path,after_path in pairs:
    before,after=rows(before_path),rows(after_path)
    assert len(before)==len(after)==24
    for a,b in zip(before,after):
        assert a['hour']==b['hour'] and a['size']==b['size']
        changes.append({'comparison':label,'hour':int(a['hour']),'rows':int(a['size']),
            'before_mae':float(a['mean']),'after_mae':float(b['mean']),
            'change_after_minus_before':float(b['mean'])-float(a['mean'])})
table(OUT/'HOURLY-CHANGES.csv',changes)
historical=[OLD/'02-01/PLAN.md',OLD/'02-01/trials.csv',OLD/'02-04/controller.py',
            OLD/'02-04/CONTROLLER-CONTRACT.md',OLD/'02-04/CONTRACT.md',OLD/'02-04/requests.csv',OLD/'02-04/trials.csv',
            *[p for _,a,b in pairs for p in (a,b)]]
table(OUT/'AUDITED-IDENTITIES.csv',[{'path':str(p),'sha256':digest(p)} for p in historical])
requests=rows(OLD/'02-04/requests.csv')
ledger=rows(OLD/'02-04/trials.csv')
source=(OLD/'02-04/controller.py').read_text(encoding='utf-8')
contract=(OLD/'02-04/CONTROLLER-CONTRACT.md').read_text(encoding='utf-8')
checks={
    'two historical fits only':len(ledger)==2 and all(r['status']=='ok' for r in ledger),
    'four historical requests':len(requests)==4,
    'duplicate refused without admission':requests[2]['attempts_before']==requests[2]['attempts_after']=='2' and requests[2]['exit_status']=='1' and 'Duplicate recipe' in requests[2]['outcome'],
    'new recipe refused at budget':requests[3]['attempts_before']==requests[3]['attempts_after']=='2' and requests[3]['model']=='forest' and 'Attempt budget exhausted' in requests[3]['outcome'],
    'controller source matches contract':digest(OLD/'02-04/controller.py') in contract,
    'duplicate check precedes fit admission':source.index('Duplicate recipe; no new fit')<source.index('row = lab.experiment'),
}
table(OUT/'HISTORICAL-CHECKS.csv',[{'check':k,'passed':v} for k,v in checks.items()])
assert all(checks.values())
fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained',sharex=True)
for ax,(label,_,_) in zip(axes,pairs):
    subset=[r for r in changes if r['comparison']==label]
    delta=[r['change_after_minus_before'] for r in subset]
    ax.bar(range(24),delta,color=['#198678' if x<0 else '#bd5a33' for x in delta])
    ax.axhline(0,color='#334155',linewidth=1)
    ax.set_ylabel('Change in hourly MAE\n(rentals per hour)')
    ax.set_title(('Constant → linear, calendar inputs (historical comparison)' if label=='Model change' else 'Calendar → calendar + weather, linear model (new comparison)'),loc='left',fontsize=11)
    ax.grid(axis='y',alpha=.2)
    ax.set_axisbelow(True)
axes[-1].set_xticks(range(24))
axes[-1].set_xlabel('Recorded hour')
fig.suptitle('A better overall score can hide worse hourly slices\nBelow zero: lower error. Above zero: higher error.',fontsize=14)
fig.savefig(OUT/'hourly-change.png',dpi=160,facecolor='white')
plt.close(fig)
lines=['# Measured slice audit','','Both panels use recorded selection errors. Each hour has 176–182 rows; the overall MAE is row-weighted, not a simple average of the 24 hourly means. No new fit or causal effect is estimated.','']
for label,_,_ in pairs:
    subset=[r for r in changes if r['comparison']==label]
    total=sum(r['rows'] for r in subset)
    before=sum(r['rows']*r['before_mae'] for r in subset)/total
    after=sum(r['rows']*r['after_mae'] for r in subset)/total
    worse=[r['hour'] for r in subset if r['change_after_minus_before']>0]
    lines += [f'- {label}: full weighted MAE {before:.9f} → {after:.9f}; worse hours {worse}.']
lines += ['','Historical model change: hour 8 remains weak at MAE 260.203781 despite improving from 324.076923. At hour 6 the linear model is worse: 59.489109 versus 47.972527. A lower full score does not mean every slice improved.','','This 02.01 analysis is retrospective. The old PLAN.md fixes the compared recipes, but does not retain a pre-fit diagnostic note. Do not present this later explanation as proof that that note governed the historical choice. The new 02.03 feedback and decisions, in contrast, were saved before their new fits.']
(OUT/'SLICE-AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Audited 48 hourly rows and six historical-controller checks; produced one measured plot. No fits.')

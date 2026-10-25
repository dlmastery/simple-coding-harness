"""Plot only recorded, comparable seed-17 development results."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();root=a.workspace
def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
first=rows(root/'10-18/experiment/trials.csv');second=rows(root/'10-19/confirmation/experiment/trials.csv')
assert first[0]['features']=='calendar' and first[1]['features']=='all' and second[0]['model']=='forest'
assert all(r['seed']=='17' for r in first+second)
assert abs(float(first[1]['score'])-float(second[1]['score']))<1e-10
records=[('Linear\ncalendar',first[0]),('Linear\ncalendar + weather',first[1]),('Forest\ncalendar + weather',second[0])]
fig,ax=plt.subplots(figsize=(10,5.8),layout='constrained');fig.patch.set_facecolor('white');ax.set_facecolor('white')
values=[float(r['score']) for _,r in records]
bars=ax.bar([label for label,_ in records],values,width=.55,color=['#a7b8c4','#599db2','#28677e'])
ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=7,fontsize=14,color='#183648')
ax.set_ylim(0,125);ax.set_ylabel('Selection MAE · rentals per hour',fontsize=12);ax.tick_params(axis='both',labelsize=12)
ax.set_title('Two task improvements; one unchanged research procedure',loc='left',fontsize=17,color='#183648',pad=26)
ax.text(0,1.02,'Train: 2011  ·  Selection: January–June 2012  ·  Seed 17  ·  Lower is better',transform=ax.transAxes,fontsize=11,color='#526977')
ax.spines[['top','right']].set_visible(False);ax.yaxis.grid(True,color='#e7edf0');ax.set_axisbelow(True)
target=root/'10-21';target.mkdir(exist_ok=True)
for suffix in ['png','svg']:fig.savefig(target/('measured-lineage.'+suffix),dpi=170)
plt.close(fig)
with (target/'PLOT-DATA.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.writer(stream,lineterminator='\n');writer.writerow(['recipe','selection_mae','seed','researcher_sha256'])
    writer.writerows([[label.replace('\n',' / '),r['score'],r['seed'],r['policy_sha256']] for label,r in records])

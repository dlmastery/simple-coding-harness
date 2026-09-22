"""Render retained measurements only; no model fitting or image generation."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

repo=Path(__file__).resolve().parents[3]
folder=repo.parent/'rsi-work-2026-09-21-dream-labs/discovery'
if (folder/'tree-v2.png').exists():raise SystemExit('Preserve rendered figure')
with (folder/'TREE.csv').open(encoding='utf-8',newline='') as stream:rows={r['node']:r for r in csv.DictReader(stream)}
fig,ax=plt.subplots(figsize=(12,6.5));fig.patch.set_facecolor('white');ax.set_axis_off();ax.set_xlim(0,1);ax.set_ylim(0,1)
positions={'R':(.11,.5),'A':(.34,.5),'B':(.61,.74),'C':(.61,.25),'D':(.87,.74)}
for node,parent in [('A','R'),('B','A'),('C','A'),('D','B')]:
    ax.add_patch(FancyArrowPatch(positions[parent],positions[node],arrowstyle='-|>',mutation_scale=16,linewidth=1.8,color='#607584',linestyle='--' if node=='D' else '-',shrinkA=45,shrinkB=95 if node=='D' else 47))
for node,(x,y) in positions.items():
    r=rows[node]
    label='R\nInitial workspace\nUnscored' if node=='R' else ('D\nForest proposal\nUNKNOWN; no fit' if node=='D' else f'{node}  {r["model"]}/all\nMAE {float(r["mae"]):.2f}\n{float(r["fit_seconds"]):.3f} fit s')
    ax.text(x,y,label,ha='center',va='center',fontsize=11,color='#143047',bbox=dict(boxstyle='round,pad=.8',facecolor='#f1f7fa' if node!='D' else '#fff8eb',edgecolor='#397291',linestyle='--' if node=='D' else '-'))
ax.text(.03,.97,'A tree backed by three measured attempts',fontsize=21,color='#143047',weight='bold',va='top')
ax.text(.03,.89,'Bike demand · selection MAE · smaller is better · seed 17',fontsize=12,color='#4c6575')
ax.text(.03,.05,'Solid arrows: recorded recipe ancestry. Dashed arrow: an unexecuted idea.\nThis is a classroom record, not the full Dream-RSI transition system.',fontsize=11,color='#4c6575')
fig.savefig(folder/'tree-v2.png',dpi=180,bbox_inches='tight');fig.savefig(folder/'tree-v2.svg',bbox_inches='tight');plt.close(fig)

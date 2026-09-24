"""Plot only the measured development outcomes retained by the generation run."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('evidence',type=Path)
args=parser.parse_args()
frame=pd.read_csv(args.evidence/'RESULTS.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
figure,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
figure.set_facecolor('white')
baseline=frame[frame.path=='baseline'].sort_values('generation')
initial=float(baseline.iloc[0].parent_selection)
retained=[initial,*baseline.retained_selection.tolist()]
axes[0].plot([0,1,2],retained,color='#176b91',linewidth=2.5,marker='o',markersize=8)
for generation,value in enumerate(retained):
    axes[0].annotate(f'{value:.2f}',(generation,value),xytext=(0,10),textcoords='offset points',ha='center')
axes[0].set(xticks=[0,1,2],xticklabels=['Start','Generation 1','Generation 2'],ylim=(85,130),ylabel='Selection MAE · rentals/hour',title='Both paths retained the same task result')
axes[0].text(.03,.06,'Tree rejected; weather feature change accepted.',transform=axes[0].transAxes,fontsize=10)
subset=frame[frame.path=='recursive']
for shift,arm,color,label in [(-.18,'active','#176b91','Active improver'),(.18,'proposed','#c78233','Proposed improver')]:
    values=subset[subset.arm==arm].sort_values('generation').retained_selection.to_numpy()
    bars=axes[1].bar([1+shift,2+shift],values,width=.33,color=color,label=label)
    axes[1].bar_label(bars,fmt='%.2f',padding=3,fontsize=10)
axes[1].set(xticks=[1,2],xticklabels=['Generation 1\nParent retained on tie','Generation 2\nMargin proposal rejected'],ylim=(0,150),ylabel='Selection MAE of retained task skill',title='Neither improver proposal was accepted')
axes[1].legend(frameon=False,loc='upper left',fontsize=10,ncols=2)
for axis in axes:
    axis.set_axisbelow(True)
    axis.grid(axis='y',color='#e4e8eb')
figure.suptitle('Two measured generations on the known bike task · lower error is better',fontsize=15,fontweight='bold')
figure.savefig(args.evidence/'generation-results.png',dpi=160,facecolor='white')

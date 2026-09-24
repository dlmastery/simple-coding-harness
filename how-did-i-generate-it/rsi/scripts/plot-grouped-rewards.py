"""Plot the executed toy update without implying GRPO or empirical rollouts."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('workspace',type=Path)
args=parser.parse_args()
cases=[('correct_rewards','Correct observed rewards'),('equal_rewards','Equal observed rewards'),('one_wrong_reward','One incorrect reward')]
summary=pd.read_csv(args.workspace/'10-24/SUMMARY.csv').set_index('case')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
figure,axes=plt.subplots(1,3,figsize=(12,4.4),layout='constrained',sharey=True)
for axis,(name,title) in zip(axes,cases):
    data=pd.read_csv(args.workspace/'10-24'/f'{name}.csv')
    colors=['#b55955','#b55955','#237f8c','#237f8c']
    if name=='one_wrong_reward':colors[0]='#cf8a2d'
    bars=axis.bar(data.action,data.new_probability*100,color=colors,width=.6)
    axis.bar_label(bars,fmt='%.2f',padding=4,fontsize=10)
    axis.axhline(25,color='#606773',linestyle='--',linewidth=1,label='Initial probability: 25%')
    axis.set(title=title,xticks=[0,1,2,3],xticklabels=['A0\ntrue 0','A1\ntrue 0','A2\ntrue 1','A3\ntrue 1'],ylim=(0,35))
    axis.set_xlabel(f'Expected true reward: {summary.loc[name,"expected_true_reward_after"]:.4f}')
    axis.grid(axis='y',color='#e5e9ec');axis.set_axisbelow(True)
axes[0].set_ylabel('Probability after one toy update (%)')
axes[1].legend(frameon=False,loc='upper center',fontsize=9)
figure.suptitle('A reward error can favor the wrong action · numerical illustration, not LLM training',fontsize=13,fontweight='bold')
figure.savefig(args.workspace/'10-24/toy-policy-update.png',dpi=160,facecolor='white')

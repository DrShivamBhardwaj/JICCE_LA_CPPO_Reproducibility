"""Unadjusted paired effect intervals; significance remains in the analysis table."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'publication/censored_feedback/figures';out.mkdir(parents=True,exist_ok=True)
a=json.loads((ROOT/'outputs/ns3_censored/paired_analysis.json').read_text());settings=['benign','blackhole','congested_benign','congested_blackhole','weaklink_benign'];labels=['Benign','Blackhole','Congested benign','Congested blackhole','Weak links benign']
plt.rcParams.update({'font.size':9,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(6.2,3.8))
for comp,offset,color,label in [('active_proof',-.11,'#1f617e','Against active proofs'),('frozen_prior',.11,'#a25536','Against frozen prior')]:
 r=[next(x for x in a if x['setting']==s and x['comparator']==comp and x['endpoint']=='delivery') for s in settings];m=np.array([x['difference'] for x in r])*100;lo=np.array([x['ci95'][0] for x in r])*100;hi=np.array([x['ci95'][1] for x in r])*100;y=np.arange(5)+offset
 ax.errorbar(m,y,xerr=[m-lo,hi-m],fmt='o',color=color,capsize=3,markersize=4,label=label)
ax.axvline(0,color='0.45',lw=.8,ls='--');ax.set_yticks(range(5),labels);ax.invert_yaxis();ax.set_xlabel('Censored minus comparator delivery (percentage points)');ax.grid(axis='x',alpha=.15);ax.legend(loc='lower center',bbox_to_anchor=(.5,1.03),frameon=False,ncol=2,fontsize=8);fig.subplots_adjust(left=.27,right=.98,bottom=.20,top=.84)
for ext in ['svg','pdf','eps','png']:fig.savefig(out/f'fig8.{ext}',dpi=900)
print(out)

"""Publication figure from audited paired contrasts only."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
r=Path(__file__).resolve().parents[1];a=json.loads((r/'outputs/cooja_feedback/primary_600/analysis.json').read_text());assert a['runs']==600
out=r/'publication/array/cooja_figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
labels={'active':'Active proofs','naive':'Naive passive','frozen':'Frozen prior','censored_proof':'Censored + proofs'};colors=['#245879','#b15b3c','#657865','#7b628a']
fig,axes=plt.subplots(2,2,figsize=(8.4,6.6),layout='constrained')
rows=[x for x in a['contrasts'] if x['endpoint']=='delivery'];limits={attack:max(1.,max(abs(v*100) for x in rows if x['attack']==attack for v in x['ci95'])*1.15) for attack in [0,1]}
for ax,(attack,timing) in zip(axes.flat,[(0,0),(0,1),(1,0),(1,1)]):
 for y,(arm,color) in enumerate(zip(labels,colors)):
  x=next(x for x in rows if (x['attack'],x['timing'],x['arm'])==(attack,timing,arm));v=x['mean_difference']*100;lo,hi=np.array(x['ci95'])*100
  ax.errorbar(v,y,xerr=np.array([[v-lo],[hi-v]]),fmt='o',color=color,markerfacecolor=color if x['p_holm']<.05 else 'white',markersize=7,capsize=4,elinewidth=2.7,markeredgewidth=1.5)
 ax.axvline(0,color='#333333',linewidth=1);ax.set_yticks(range(4),list(labels.values()));ax.invert_yaxis();ax.set_xlim(-limits[attack],limits[attack]);ax.grid(axis='x',alpha=.2);ax.set_title(('Benign' if attack==0 else 'Blackhole')+'\n'+('No added compute delay' if timing==0 else 'Scheduled processing delays'),fontsize=11);ax.set_xlabel('Arm minus censored delivery\n(percentage points)',fontsize=11)
fig.legend(handles=[Line2D([0],[0],marker='o',linestyle='',color='#333333',markerfacecolor='#333333',label='Holm p < 0.05'),Line2D([0],[0],marker='o',linestyle='',color='#333333',markerfacecolor='white',label='Holm p ≥ 0.05')],loc='outside lower center',ncol=2,frameon=False)
for ext in ['png','pdf','svg']:fig.savefig(out/f'fig12_cooja_paired_delivery.{ext}',dpi=600 if ext=='png' else None,bbox_inches='tight')
svg=out/'fig12_cooja_paired_delivery.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
plt.close(fig);print(out)

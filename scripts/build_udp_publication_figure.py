from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'publication/updated_evidence/figures';OUT.mkdir(exist_ok=True,parents=True)
x=pd.read_csv(ROOT/'outputs/udp_matched_comparison/paired_seed_summary.csv').set_index('seed')
plt.rcParams.update({'font.size':9,'svg.fonttype':'none'})
fig,axs=plt.subplots(1,2,figsize=(6.8,2.8),layout='constrained')
for _,r in x.iterrows():axs[0].plot([0,1],[r.capacity_mlp,r.attention],color='#a0a0a0',lw=.7)
axs[0].scatter(np.zeros(len(x)),x.capacity_mlp,s=12,color='#555555');axs[0].scatter(np.ones(len(x)),x.attention,s=12,color='#21618c')
axs[0].set(xticks=[0,1],xticklabels=['Capacity MLP','Attention'],ylabel='Sink delivery fraction',ylim=(-.03,1.03),title='(a) Paired fixture outcomes')
axs[1].scatter(x.index-73000,x.attention_minus_mlp,s=13,color='#21618c');axs[1].axhline(0,color='black',lw=.8);axs[1].axhline(x.attention_minus_mlp.mean(),color='#9a5c32',lw=1)
axs[1].set(xlabel='Fixture index',ylabel='Attention − MLP',title='(b) Delivery difference')
for a in axs:a.spines[['top','right']].set_visible(False);a.grid(axis='y',alpha=.15)
for ext in ['svg','pdf','eps']:fig.savefig(OUT/f'fig7.{ext}',bbox_inches='tight')
fig.savefig(OUT/'fig7.png',dpi=900,bbox_inches='tight');plt.close(fig)

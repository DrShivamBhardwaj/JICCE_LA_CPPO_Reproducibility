"""Exact vector figures for the authenticated transfer and virtual interface."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'publication/array/figures';out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})

fig,ax=plt.subplots(figsize=(9,6.5));ax.set(xlim=(0,9),ylim=(-1.5,5));ax.axis('off')
def box(x,y,w,h,title,detail,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.04,rounding_size=.08',facecolor=color,edgecolor='#496579',linewidth=1.5))
 ax.text(x+w/2,y+h*.68,title,ha='center',va='center',weight='bold',fontsize=10)
 ax.text(x+w/2,y+h*.28,detail,ha='center',va='center',fontsize=9,linespacing=1.4)
def arrow(a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#496579',lw=1.7))
ax.text(.15,4.8,'(a) Authenticated routing at each host node',weight='bold')
box(.15,3.3,2.5,1.1,'Received wire state','HMAC, boot session\nsequence and freshness','#e6f0f5')
box(3.2,3.3,2.5,1.1,'Local observation','93 features from cache,\nACKs, LQI and class debt','#edf3e7')
box(6.25,3.3,2.5,1.1,'Frozen policy','Attention / MLP\nor greedy control','#eae9f4')
arrow((2.7,3.85),(3.13,3.85));arrow((5.75,3.85),(6.18,3.85))
ax.text(4.45,2.85,'Data: source HMAC + hop tag   |   Receipt: sink Ed25519 signature',ha='center',fontsize=10)
ax.text(.15,2.25,'(b) Virtual serial interface and modeled radio',weight='bold')
labels=[('Host adapter','Actual Python\nprocess'),('Virtual UART','PTY serial port\nJSON commands'),('Firmware API','TX, RX, ACK\ntelemetry contract'),('Radio engine','ns-3.44\nbyte frames')]
for i,(title,detail) in enumerate(labels):box(.15+i*2.25,.85,2.0,1.05,title,detail,'#f1f3f5')
for i in range(3):arrow((2.2+i*2.25,1.38),(2.35+i*2.25,1.38))
ax.text(.15,.25,'(c) Compiled MCU backend: four CC2538 boards in Renode',weight='bold')
for i,(title,detail) in enumerate([('Host adapter','Routing inference\nand cryptography'),('Emulated UART','Actual firmware\nJSON parser'),('Cortex-M3 MCU','Compiled C: FIFO\nand MAC ACKs'),('802.15.4 model','Range medium\nvirtual radio')]):box(.15+i*2.25,-1.0,2.0,.95,title,detail,'#e6f0f5')
for i in range(3):arrow((2.2+i*2.25,-.53),(2.35+i*2.25,-.53))
ax.text(4.5,-1.4,'Virtual backends; no physical RF or calibrated power measurement',ha='center',fontsize=9,color='#555555')
fig.tight_layout()
for ext in ['svg','pdf','png']:fig.savefig(out/f'fig7_authenticated_virtual.{ext}',dpi=600,bbox_inches='tight',facecolor='white')
plt.close(fig)

rows=json.loads((ROOT/'outputs/auth_policy/summary.json').read_text());analysis=json.loads((ROOT/'outputs/auth_policy/analysis.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(9,6.3),gridspec_kw={'width_ratios':[1.15,1]})
colors=['#657b83','#b7803a','#347c8c'];arms=['greedy','mlp','attention']
for row,setting in enumerate(['benign','selective_drop']):
 ax=axes[row,0];arr=np.array([[next(r['delivery']*100 for r in rows if r['seed']==s and r['arm']==arm and r['setting']==setting) for arm in arms] for s in range(83001,83031)])
 for sample in arr:ax.plot(range(3),sample,color='#bfc7cc',alpha=.45,lw=.7,zorder=1)
 for col in range(3):
  ax.scatter(col+np.linspace(-.065,.065,30),arr[:,col],s=13,color=colors[col],alpha=.65,zorder=2)
  ax.scatter(col,arr[:,col].mean(),s=75,marker='D',color=colors[col],edgecolor='white',zorder=3)
 ax.set(xticks=range(3),xticklabels=['Greedy','MLP','Attention'],ylabel='Delivery (%)',title=('(a) Benign' if row==0 else '(c) Selective dropping'),ylim=(25,102));ax.grid(axis='y',alpha=.15)
 ax=axes[row,1]
 for y,comp in enumerate(['greedy','mlp']):
  e=next(e for e in analysis['effects'] if e['setting']==setting and e['endpoint']=='delivery' and e['comparator']==comp)
  v=e['difference']*100;lo,hi=np.array(e['ci95'])*100
  ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=colors[2],capsize=4,lw=2)
 ax.axvline(0,color='#687680',ls='--',lw=1);ax.set(yticks=[0,1],yticklabels=['vs Greedy','vs MLP'],ylim=(-.6,1.6),xlim=(-7,5),xlabel='Attention delivery difference (points)',title='(b) Paired 95% intervals' if row==0 else '(d) Paired 95% intervals');ax.grid(axis='x',alpha=.15)
fig.tight_layout(h_pad=2,w_pad=2)
for ext in ['svg','pdf','png']:fig.savefig(out/f'fig8_policy_transfer.{ext}',dpi=600,bbox_inches='tight',facecolor='white')

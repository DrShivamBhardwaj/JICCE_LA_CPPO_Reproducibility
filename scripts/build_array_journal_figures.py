"""Array vector artwork from frozen observations; no fabricated/smoothed data."""
from pathlib import Path
import json,hashlib,io,os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle,Polygon,Circle,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'publication/array/figures';OUT.mkdir(exist_ok=True)
QA=ROOT.parent/'array_journal_figure_qa';QA.mkdir(exist_ok=True)
INPUTS=['outputs/ns3_censored/summary.json','outputs/ns3_censored/paired_analysis.json','outputs/ns3_censored/implementation_audit.json','outputs/auth_policy/summary.json','outputs/auth_policy/analysis.json','outputs/renode_boards/audit.json']
rows,analysis,audit,transfer,ta,mcu=[json.loads((ROOT/p).read_text()) for p in INPUTS]
C={'censored_passive':'#007E87','active_proof':'#CA6940','naive_passive':'#A07824','frozen_prior':'#68758A','capacity_mlp_censored':'#8665A6','greedy':'#68758A','mlp':'#B17C24','attention':'#007E87'}
L={'censored_passive':'Censored passive','active_proof':'Active proofs','naive_passive':'Naive passive','frozen_prior':'Frozen prior','capacity_mlp_censored':'Capacity MLP','greedy':'Greedy','mlp':'MLP','attention':'Attention'}
SETS=['benign','blackhole','congested_benign','congested_blackhole','weaklink_benign'];SL=['Benign','Blackhole','Congested benign','Congested blackhole','Weak links benign']
INK='#243746';MUTED='#617382';GRID='#E3E9ED';TEAL='#E7F3F3';BLUE='#EAF1F8';SAND='#FBF1E4';PURPLE='#F0ECF7'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.labelsize':11,'axes.titlesize':12,'axes.titleweight':'bold','axes.labelcolor':INK,'text.color':INK,'xtick.color':MUTED,'ytick.color':INK,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#AAB7C1','axes.linewidth':.8,'lines.linewidth':2,'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white'})
exhibits={}
def save(fig,name):
 for ext in ['svg','pdf','png']:
  buffer=io.BytesIO();fig.savefig(buffer,format=ext,dpi=600,bbox_inches='tight',pad_inches=.13)
  target=OUT/f'{name}.{ext}';tmp=target.with_suffix('.tmp');tmp.write_bytes(buffer.getvalue());os.replace(tmp,target)
  if ext=='png':
   from PIL import Image
   Image.open(target).verify()
 fig.savefig(QA/f'{name}.png',dpi=150,bbox_inches='tight',pad_inches=.13);plt.close(fig)
def canvas(h=6.2):
 f,ax=plt.subplots(figsize=(9.2,h));ax.set(xlim=(0,100),ylim=(-8,100));ax.axis('off');return f,ax
def box(ax,x,y,w,h,title,detail='',color=BLUE,fs=11):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.25,rounding_size=1.2',fc=color,ec='#90A4B1',lw=1.25))
 ax.text(x+w/2,y+h*(.69 if detail else .5),title,ha='center',va='center',fontsize=fs,weight='bold')
 if detail:ax.text(x+w/2,y+h*.29,detail,ha='center',va='center',fontsize=fs-1,linespacing=1.45)
def arrow(ax,a,b,label='',color=MUTED,style='-',rad=0):
 ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,lw=2,color=color,linestyle=style,connectionstyle=f'arc3,rad={rad}'))
 if label:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+1.5,label,ha='center',fontsize=9,color=color,bbox=dict(fc='white',ec='none',pad=1))
def heading(ax,y,text):ax.text(1,y,text,weight='bold',fontsize=12,va='center')
def footer(ax,text):ax.text(.5,-.20,text,transform=ax.transAxes,ha='center',va='top',fontsize=9,color=MUTED)
def null(ax):ax.axvline(0,color='#81939F',lw=1.2,ls=(0,(4,3)),zorder=0);ax.grid(axis='x',color=GRID,lw=.8);ax.set_axisbelow(True)
# 1 — explicit computational and radio boundaries, with a topology inset.
f,ax=canvas(6.3)
heading(ax,98,'(a) Frozen feedback benchmark: controller and state boundary')
ax.add_patch(FancyBboxPatch((.5,44),99,48,boxstyle='round,pad=.2,rounding_size=1.5',fc='#F8FAFC',ec='#9EB0BC',ls='--',lw=1.2))
box(ax,3,69,27,17,'Local observation','13 context values\n8 × 10 candidate features')
box(ax,36,69,28,17,'Frozen policy','Shared encoders\nmasked candidate scoring',PURPLE)
box(ax,70,69,27,17,'Relay decision','Masked argmax\nfixed checkpoint',TEAL)
arrow(ax,(30,78),(36,78));arrow(ax,(64,78),(70,78))
box(ax,3,47,27,16,'Beacon cache','Receive-gated metadata')
box(ax,36,47,28,16,'Observer ledger','ACK gate · strongest credit',TEAL)
box(ax,70,47,27,16,'Shared route state','Visited set · reverse path',SAND)
arrow(ax,(16,63),(16,69));arrow(ax,(50,63),(50,69));arrow(ax,(84,69),(84,63))
heading(ax,36,'(b) IEEE 802.15.4 radio')
for x,n in [(12,'u'),(48,'v'),(84,'w')]:
 ax.add_patch(Circle((x,18),6,fc=TEAL,ec=C['censored_passive'],lw=2));ax.text(x,18,n,ha='center',va='center',weight='bold',fontsize=15)
ax.text(12,6,'Observer',ha='center',fontsize=10);ax.text(48,6,'Selected relay',ha='center',fontsize=10);ax.text(84,6,'Next hop',ha='center',fontsize=10)
arrow(ax,(18,18),(42,18),'DATA + MAC ACK');arrow(ax,(54,18),(78,18),'Forward attempt')
arrow(ax,(48,25),(48,44));ax.text(52,37,'Received events',ha='left',va='center',fontsize=9,color=MUTED);arrow(ax,(90,47),(90,26),'TX request')
ax.text(50,-1,'Cache geometry and reverse-route state remain simulator-side in this benchmark.',ha='center',fontsize=10,color=MUTED)
save(f,'fig1_architecture')
# 2 — ACK-gated state transition with explicit censored branches.
f,ax=canvas(7.2)
heading(ax,98,'ACK-gated evidence and credit lifecycle')
box(ax,23,79,51,13,'Register observer–relay–packet record','Expected link success q\nRetain strongest observation')
arrow(ax,(48.5,79),(48.5,75))
ax.add_patch(Polygon([(48.5,75),(65,64),(48.5,53),(32,64)],fc=PURPLE,ec='#90A4B1',lw=1.3));ax.text(48.5,64,'First-hop\nMAC ACK?',ha='center',va='center',weight='bold',fontsize=11)
box(ax,78,57,21,14,'Censor','No positive credit',SAND,10);arrow(ax,(65,64),(78,64),'Failure')
arrow(ax,(48.5,53),(48.5,48),'Success')
box(ax,23,35,51,13,'Retain strongest matched observation','Overheard forward = 0.5  ·  Sink receipt = 1.0',TEAL)
box(ax,1,36,18,13,'No evidence','150 ms expiry',SAND,10);arrow(ax,(23,41.5),(19,41.5))
arrow(ax,(48.5,35),(48.5,26))
box(ax,23,13,51,13,'Apply only the unseen credit increment','ACK-gated clipped weight; failure prior stays at 1',TEAL)
box(ax,1,14,18,13,'Censor timeout','Late receipt\ncan upgrade',SAND,9.5);arrow(ax,(10,36),(10,27));arrow(ax,(19,20),(23,20),style='--')
arrow(ax,(48.5,13),(48.5,8));box(ax,23,-3,51,11,'Update next routing decision','Same frozen policy; no retraining',BLUE,10.5)
save(f,'fig2_algorithm_flow')
# 3 — experimental accounting, with excluded pilot shown separately.
f,ax=canvas(6.8)
for y,h,label in [(77,19,'DEVELOP'),(55,17,'FREEZE'),(24,26,'EVALUATE'),(1,18,'AUDIT')]:
 ax.add_patch(Rectangle((0,y),12,h,fc=BLUE,ec='none'));ax.text(6,y+h/2,label,rotation=90,ha='center',va='center',weight='bold',fontsize=10)
box(ax,18,78,49,18,'30 training fixtures','41001–41030\nAttention + capacity-matched MLP checkpoints')
box(ax,73,78,26,18,'600 development runs','76001–76030\nHistorical outcomes retained',SAND,10)
arrow(ax,(67,87),(73,87));arrow(ax,(42.5,78),(42.5,72))
box(ax,18,55,49,17,'Protocol and source locked','Commit 4027f07 · before holdout outcomes',PURPLE)
box(ax,73,55,26,17,'Technical pilot','76901\nExcluded from inference',SAND,10)
arrow(ax,(42.5,55),(42.5,49))
box(ax,18,24,49,25,'750 retained holdout runs','30 new fixtures: 77001–77030\n× 5 settings × 5 feedback / policy arms\n45,000 source packets',TEAL,11)
box(ax,73,28,26,17,'Frozen inference','60-test Holm family\n4 required gate checks',PURPLE,10);arrow(ax,(67,36.5),(73,36.5))
arrow(ax,(42.5,24),(42.5,19));box(ax,18,1,81,18,'Trace and endpoint reconciliation','30 compressed streams · all 750 runs retained · no holdout run exclusions',TEAL)
ax.text(50,-5,'Experimental protocol pipeline · source freeze and complete run accounting.',ha='center',fontsize=9,color=MUTED)
save(f,'fig3_evaluation_flow')
# 4 — separate comparison panels with exact estimates and intervals.
f,axes=plt.subplots(1,2,figsize=(9.2,4.9),sharey=True);exhibits['fig4']=[]
for j,comp in enumerate(['active_proof','frozen_prior']):
 ax=axes[j];vals=[next(x for x in analysis if x['setting']==s and x['comparator']==comp and x['endpoint']=='delivery') for s in SETS]
 means=np.array([x['difference'] for x in vals])*100;cis=np.array([x['ci95'] for x in vals])*100
 for y,(v,(lo,hi)) in enumerate(zip(means,cis)):
  ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o' if j==0 else 's',color=C[comp],capsize=4,ms=7,elinewidth=2,zorder=3)
  ax.annotate(f'{v:+.2f}',(v,y),xytext=(0,11),textcoords='offset points',ha='center',fontsize=9,color=C[comp])
 ax.set_title(f'({chr(97+j)}) Versus {L[comp].lower()}',loc='left',pad=17);ax.set_xlabel('Delivery difference (percentage points)');null(ax);ax.set_ylim(4.55,-.65);ax.set_xlim(-2,9);ax.locator_params(axis='x',nbins=4)
 exhibits['fig4'] += [dict(setting=s,comparator=comp,mean_pp=float(v),ci95_pp=[float(x) for x in ci]) for s,v,ci in zip(SETS,means,cis)]
axes[0].set_yticks(range(5),SL);f.subplots_adjust(left=.24,right=.98,wspace=.24,bottom=.22,top=.82)
f.text(.59,.035,'Censored passive − comparator  |  paired t intervals, 30 fixtures per setting; identical horizontal scales',ha='center',fontsize=9,color=MUTED)
save(f,'fig4_delivery_effects')
# 5 — paired observations and all blackhole control contrasts, no density smoothing.
f,axes=plt.subplots(1,2,figsize=(9.2,5.0),gridspec_kw={'width_ratios':[1,1.65]})
a=np.array([next(r['delivery'] for r in rows if r['seed']==s and r['setting']=='blackhole' and r['arm']=='active_proof') for s in range(77001,77031)])*100
b=np.array([next(r['delivery'] for r in rows if r['seed']==s and r['setting']=='blackhole' and r['arm']=='censored_passive') for s in range(77001,77031)])*100
ax=axes[0];jitter=np.linspace(-.07,.07,30)
for i in range(30):ax.plot([jitter[i],1+jitter[i]],[a[i],b[i]],color='#B8C5CC',lw=1,alpha=.65,zorder=1)
for x,v,arm in [(0,a,'active_proof'),(1,b,'censored_passive')]:
 ax.scatter(x+jitter,v,s=24,color=C[arm],alpha=.8,edgecolors='white',linewidths=.35,zorder=2);ax.scatter(x,v.mean(),marker='D',s=85,color=C[arm],edgecolors='white',lw=1,zorder=4);ax.text(x,94,f'{v.mean():.2f}%',ha='center',weight='bold',color=C[arm])
ax.set(xticks=[0,1],xticklabels=['Active\nproofs','Censored\npassive'],ylabel='Delivery (%)',ylim=(53,98),xlim=(-.3,1.3));ax.set_title('(a) All paired fixtures',loc='left',pad=16);ax.grid(axis='y',color=GRID)
ax=axes[1];comps=['active_proof','naive_passive','frozen_prior','capacity_mlp_censored'];exhibits['fig5']=[]
for y,comp in enumerate(comps):
 z=next(x for x in analysis if x['setting']=='blackhole' and x['endpoint']=='delivery' and x['comparator']==comp);v=100*z['difference'];lo,hi=np.array(z['ci95'])*100
 ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=C[comp],capsize=4,ms=7,elinewidth=2);ax.text(9.1,y,f'{v:+.2f}  [{lo:+.2f}, {hi:+.2f}]',va='center',fontsize=9,color=C[comp]);exhibits['fig5'].append(dict(comparator=comp,mean_pp=v,ci95_pp=[lo,hi]))
null(ax);ax.set(yticks=range(4),yticklabels=[L[c] for c in comps],ylim=(3.6,-.6),xlim=(-3.3,8.5),xlabel='Delivery difference (percentage points)');ax.set_title('(b) Matched control effects',loc='left',pad=16)
f.subplots_adjust(left=.08,right=.72,bottom=.21,top=.82,wspace=.85);f.text(.76,.84,'Mean [95% interval]',fontsize=9,color=MUTED);f.text(.5,.035,'30 blackhole fixtures  ·  Diamonds: means  ·  Bars: unadjusted paired t intervals',ha='center',fontsize=9,color=MUTED)
save(f,'fig5_blackhole_estimation')
# 6 — preserve the distinction between total energy, efficiency and traffic.
f,axes=plt.subplots(1,3,figsize=(9.2,4.8),sharey=True);exhibits['fig6']=[]
for ax,metric,scale,title,label in zip(axes,['radio_energy_j','energy_per_delivered_byte','phy_tx_frames'],[1000,1000,1],['(a) Total radio\nenergy (mJ)','(b) Energy per\ndelivered byte (mJ/byte)','(c) PHY\ntransmissions (frames)'],['Difference (mJ)','Difference (mJ/byte)','Difference (frames)']):
 zz=[next(x for x in audit['contrasts'] if x['setting']==s and x['metric']==metric) for s in SETS]
 for y,z in enumerate(zz):
  v=z['difference']*scale;lo,hi=np.array(z['ci95'])*scale;ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=C['censored_passive'],capsize=4,ms=6,elinewidth=2)
  exhibits['fig6'].append(dict(setting=SETS[y],metric=metric,display_scale=scale,difference=float(v),ci95=[float(lo),float(hi)]))
 null(ax);ax.set_title(title,loc='left',fontsize=10.5,pad=18);ax.set_xlabel(label,fontsize=10);ax.locator_params(axis='x',nbins=3);ax.set_ylim(4.55,-.55)
axes[0].set_yticks(range(5),SL);f.subplots_adjust(left=.21,right=.99,wspace=.25,bottom=.25,top=.80)
f.text(.60,.07,'Censored passive − active proofs  |  30 paired fixtures per setting',ha='center',fontsize=9,color=MUTED)
f.text(.60,.015,f'Modeled receive/listen share: {100*audit["mean_listen_rx_fraction"]:.2f}%  ·  Radio-only model; no measured board energy',ha='center',fontsize=9,color=MUTED)
save(f,'fig6_energy_attribution')
# 7 — host authentication and two virtual transport backends.
f,ax=canvas(7.0);heading(ax,98,'(a) Authenticated host processing at each node')
for x,title,detail,col in [(1,'Wire validation','Pairwise HMAC · boot session\nreplay window · freshness',BLUE),(35,'Local observation','93 features from cache\nMAC ACKs · LQI · class debt',TEAL),(69,'Frozen routing','Attention / MLP / greedy\nshared strict-progress mask',PURPLE)]:box(ax,x,76,30,17,title,detail,col,10.5)
arrow(ax,(31,84.5),(35,84.5));arrow(ax,(65,84.5),(69,84.5))
ax.text(50,69,'DATA: source HMAC + hop tag   |   RECEIPT: sink Ed25519 signature   |   ≤114 application bytes',ha='center',fontsize=10)
heading(ax,59,'(b) Virtual API backend: no MCU instruction execution')
for x,title,detail in [(1,'Host adapter','Actual Python process'),(35,'PTY serial interface','TX / RX / ACK / telemetry'),(69,'ns-3.44 radio','Byte-serialized frames')]:box(ax,x,39,30,15,title,detail,BLUE,10.5)
arrow(ax,(31,46.5),(35,46.5));arrow(ax,(65,46.5),(69,46.5))
heading(ax,29,'(c) Host-controlled radio bridge · Renode 1.17.0')
for x,title,detail,col in [(1,'HOST PC','PyTorch inference · HMAC\nEd25519 signing / verification',BLUE),(35,'EMULATED MCU','C UART / radio FIFO bridge\nNo inference or crypto',TEAL),(69,'802.15.4 range model','Four virtual boards\ndeterministic reachability',SAND)]:box(ax,x,8,30,16,title,detail,col,10.5)
arrow(ax,(31,16),(35,16));arrow(ax,(65,16),(69,16))
ax.text(50,0,'Strict controls: 10/10 delivery + 10 accepted source receipts for each policy; five probes per run.',ha='center',fontsize=10,color=C['censored_passive'])
ax.text(50,-5,'No embedded inference/crypto, calibrated current or physical RF claim.',ha='center',fontsize=10,color=MUTED)
save(f,'fig7_authenticated_virtual')
# 8 — show every paired fixture and exploratory transfer intervals.
f,axes=plt.subplots(2,2,figsize=(9.2,7.8),gridspec_kw={'width_ratios':[1.1,1]});exhibits['fig8']=[]
for row,setting in enumerate(['benign','selective_drop']):
 ax=axes[row,0];arms=['greedy','mlp','attention'];arr=np.array([[next(r['delivery']*100 for r in transfer if r['seed']==seed and r['arm']==arm and r['setting']==setting) for arm in arms] for seed in range(83001,83031)])
 jitter=np.linspace(-.055,.055,30)
 for i,v in enumerate(arr):ax.plot(np.arange(3)+jitter[i],v,color='#BCC8CF',alpha=.50,lw=1)
 for col,arm in enumerate(arms):
  ax.scatter(col+jitter,arr[:,col],color=C[arm],s=20,edgecolors='white',linewidths=.3,zorder=3);ax.scatter(col,arr[:,col].mean(),marker='D',s=72,color=C[arm],edgecolors='white',zorder=4);ax.text(col,104,f'{arr[:,col].mean():.2f}%',ha='center',weight='bold',color=C[arm],fontsize=10)
 ax.set(xticks=range(3),xticklabels=['Greedy','MLP','Attention'],ylabel='Delivery (%)',ylim=(25,110),xlim=(-.3,2.3));ax.set_title(f'({chr(97+2*row)}) '+('Benign' if row==0 else 'Selective dropping'),loc='left',pad=14);ax.grid(axis='y',color=GRID)
 ax=axes[row,1]
 for y,comp in enumerate(['greedy','mlp']):
  z=next(e for e in ta['effects'] if e['setting']==setting and e['endpoint']=='delivery' and e['comparator']==comp);v=z['difference']*100;lo,hi=np.array(z['ci95'])*100
  ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=C['attention'],capsize=4,ms=7,elinewidth=2);ax.text(v,y+.22,f'{v:+.2f} [{lo:+.2f}, {hi:+.2f}]',ha='center',fontsize=9,color=C['attention']);exhibits['fig8'].append(dict(setting=setting,comparator=comp,mean_pp=v,ci95_pp=[float(lo),float(hi)]))
 null(ax);ax.set(yticks=[0,1],yticklabels=['vs Greedy','vs MLP'],ylim=(1.6,-.55),xlim=(-7.1,5.2),xlabel='Attention delivery difference (points)');ax.set_title(f'({chr(98+2*row)}) Paired transfer effects',loc='left',pad=14)
f.subplots_adjust(left=.08,right=.98,wspace=.40,hspace=.52,bottom=.15,top=.90)
f.text(.5,.06,'30 fixtures per condition · Exploratory paired bootstrap, 10,000 resamples · 95% intervals',ha='center',fontsize=9,color=MUTED)
f.text(.5,.015,'Every delivery-effect interval crosses zero; no attention-superiority claim is established.',ha='center',fontsize=10,color=INK)
save(f,'fig8_policy_transfer')
# Exact numbers and source fingerprints make visual editing auditable.
(OUT/'plotted_values.json').write_text(json.dumps(exhibits,indent=2)+'\n')
(OUT/'figure_provenance.json').write_text(json.dumps({'inputs':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},'figures':8,'formats':['svg','pdf','png'],'png_dpi':600,'style':'Vector diagrams and exact paired observations/intervals. No bitmap generative images, fabricated observations or data smoothing.','statistics':'Figures 4–6: retained unadjusted paired t intervals; original Holm decision rule unchanged. Figure 8: retained exploratory paired percentile bootstrap intervals. No new tests.','figure3':'Experimental protocol pipeline with complete retained-run accounting.','literature_review':'SciSpace search and limitations extraction informed the separation of modeled energy and emulated execution; external studies are not used as baseline data.'},indent=2)+'\n')
print(OUT)

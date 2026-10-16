"""Publication vector diagrams and paired estimation graphics from frozen outputs."""
from pathlib import Path
import io,json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Polygon,FancyArrowPatch,Rectangle
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'publication/redesigned/figures';OUT.mkdir(parents=True,exist_ok=True)
rows=json.loads((ROOT/'outputs/ns3_censored/summary.json').read_text());analysis=json.loads((ROOT/'outputs/ns3_censored/paired_analysis.json').read_text());audit=json.loads((ROOT/'outputs/ns3_censored/implementation_audit.json').read_text())
C={'censored_passive':'#176b87','naive_passive':'#9b6b36','active_proof':'#b75248','frozen_prior':'#6a7181','capacity_mlp_censored':'#795aa0'}
LABEL={'censored_passive':'Censored passive','naive_passive':'Naive passive','active_proof':'Active proofs','frozen_prior':'Frozen prior','capacity_mlp_censored':'Capacity MLP'}
SET=['benign','blackhole','congested_benign','congested_blackhole','weaklink_benign'];SL=['Benign','Blackhole','Congested benign','Congested blackhole','Weak links benign']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'axes.titlesize':10,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'lines.linewidth':2,'svg.fonttype':'none','pdf.fonttype':42})
def save(fig,name):
 for ext in ['svg','pdf','png']:
  buffer=io.BytesIO();fig.savefig(buffer,format=ext,dpi=900,facecolor='white',bbox_inches='tight',pad_inches=.08)
  data=buffer.getvalue();target=OUT/f'{name}.{ext}';temporary=target.with_suffix('.tmp');temporary.write_bytes(data);temporary.replace(target)
  assert target.stat().st_size==len(data)
 preview=ROOT.parent/'redesigned_figure_qa';preview.mkdir(exist_ok=True)
 buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=200,facecolor='white',bbox_inches='tight',pad_inches=.08);(preview/f'{name}.png').write_bytes(buffer.getvalue())
 plt.close(fig)
def canvas(w=7,h=4):
 f,ax=plt.subplots(figsize=(w,h));ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off');return f,ax
def box(ax,x,y,w,h,title,detail='',color='#edf4f7',edge='#66717c',fs=8):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.25,rounding_size=1',fc=color,ec=edge,lw=.9));ax.text(x+w/2,y+h*(.66 if detail else .5),title,ha='center',va='center',fontsize=fs,fontweight='bold');
 if detail:ax.text(x+w/2,y+h*.28,detail,ha='center',va='center',fontsize=fs-1)
def arrow(ax,start,end,label='',dashed=False,color='#5d6974',rad=0):
 ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=10,lw=1.2,color=color,linestyle='--' if dashed else '-',connectionstyle=f'arc3,rad={rad}'))
 if label:ax.text((start[0]+end[0])/2,(start[1]+end[1])/2+2,label,ha='center',va='bottom',fontsize=7.5,color=color,bbox=dict(fc='white',ec='none',pad=.4))
# Fig 1 architecture: exact boundary between receive-gated state and serialized radio.
f,ax=canvas(7,4.7)
ax.add_patch(Rectangle((1,43),98,55,fill=False,ec='#9ba7b2',lw=.8,ls='--'));ax.text(3,95,'PYTHON CONTROLLER AND SIMULATOR STATE',fontsize=8,color='#52616f')
box(ax,5,71,26,17,'Local observation','13 context; 8 candidates');box(ax,38,71,25,17,'Frozen policy','Shared encoders');box(ax,70,71,25,17,'Relay choice','Masked argmax')
arrow(ax,(31,80),(38,80));arrow(ax,(63,80),(70,80))
box(ax,5,48,26,16,'Beacon cache','Receive gated sidecar');box(ax,38,48,25,16,'Observer ledger','ACK gate; unique credit');box(ax,70,48,25,16,'Shared route state','Visited set; reverse path',color='#faf3e9')
arrow(ax,(18,64),(18,71));arrow(ax,(50,64),(44,71));arrow(ax,(82,71),(82,64));arrow(ax,(70,56),(63,56),dashed=True)
ax.add_patch(Rectangle((1,4),98,33,fill=False,ec='#9ba7b2',lw=.8));ax.text(3,33,'NS 3 IEEE 802.15.4 RADIO',fontsize=8,color='#52616f')
for x,title in [(6,'Observer u'),(38,'Relay v'),(70,'Next hop w')]:box(ax,x,13,24,12,title,color='#eef4ee')
arrow(ax,(30,19),(38,19),'data + MAC ACK');arrow(ax,(62,19),(70,19),'forward attempt');arrow(ax,(50,25),(50,48),'received events');arrow(ax,(18,37),(18,48),dashed=True);arrow(ax,(82,48),(82,37),'send request')
ax.text(50,7,'Overheard frames and reverse receipts cross the actual radio channel',ha='center',fontsize=7.8)
save(f,'fig1_architecture')
# Fig 2 event algorithm, staged boxes with explicit ACK and evidence branches.
f,ax=canvas(7,5.3)
for y,label in [(83,'Register'),(60,'Eligibility'),(35,'Evidence'),(7,'Close')]:ax.text(1,y+4,label,rotation=90,va='center',fontsize=8,color='#64717d')
box(ax,28,83,42,12,'Register observer relay packet','Store expected link success q')
arrow(ax,(49,83),(49,77));diamond=np.array([[49,77],[65,67],[49,57],[33,67]]);ax.add_patch(Polygon(diamond,fc='#f3f5f7',ec='#66717c',lw=.9));ax.text(49,67,'First hop ACK?',ha='center',va='center',fontsize=8.5)
box(ax,75,60,23,14,'Censor','No positive credit',color='#faf3e9',fs=8);arrow(ax,(65,67),(75,67),'failed')
arrow(ax,(49,57),(49,51),'success');box(ax,28,38,42,13,'Accept strongest observation','Overhear 0.5   receipt 1.0');arrow(ax,(49,38),(49,31));box(ax,28,18,42,13,'Credit only unseen increment','Clip weighted update; keep failure prior')
box(ax,75,36,23,15,'No observation','Expire after 150 ms',color='#faf3e9',fs=8);arrow(ax,(70,45),(75,45),'missing');arrow(ax,(86,36),(86,24));box(ax,75,9,23,15,'Censor timeout','Late receipt eligible',color='#faf3e9',fs=8)
arrow(ax,(49,18),(49,13));box(ax,28,1,42,12,'Update routing score','Same frozen policy at next decision');arrow(ax,(75,16),(70,24),dashed=True)
ax.text(49,99,'Censored passive arm',ha='center',fontsize=10,fontweight='bold');save(f,'fig2_algorithm_flow')
# Fig 3 PRISMA-inspired stage rail, no literature screening claim.
f,ax=canvas(7,5.5)
for y,h,label in [(77,21,'Development'),(55,17,'Freeze'),(20,29,'Holdout'),(1,13,'Audit')]:
 ax.add_patch(Rectangle((1,y),11,h,fc='#eef2f5',ec='none'));ax.text(6.5,y+h/2,label,rotation=90,ha='center',va='center',fontsize=8)
box(ax,20,83,48,14,'Training fixtures 41001 to 41030','30 paired attention and MLP checkpoints')
box(ax,74,81,24,16,'Development 760xx','600 runs retained\nin historical record',fs=8);arrow(ax,(68,90),(74,90))
arrow(ax,(44,83),(44,73));box(ax,20,56,48,17,'Design locked before outcomes','Protocol and source commit 4027f07');ax.plot([86,71,71],[81,81,66],color='#5d6974',lw=1.2,ls='--');arrow(ax,(71,66),(68,66),dashed=True)
box(ax,74,56,24,17,'Technical pilot','76901 excluded\nfrom inference',color='#faf3e9',fs=8)
arrow(ax,(44,56),(44,49));box(ax,20,34,48,15,'New fixtures 77001 to 77030','30 fixtures × 5 settings × 5 arms');arrow(ax,(44,34),(44,29));box(ax,20,16,48,13,'750 runs retained','45,000 source packets; zero run exclusions')
arrow(ax,(44,16),(44,13));box(ax,20,1,48,12,'Trace and endpoint audits','30 complete compressed streams');box(ax,74,17,24,19,'Frozen decision','60 test Holm family\n4 required gate checks',fs=8);arrow(ax,(68,23),(74,26))
save(f,'fig3_evaluation_flow')
# Fig 4 five-setting delivery contrasts, shared units and null line.
f,ax=plt.subplots(figsize=(6.5,3.7))
for comp,offset,marker in [('active_proof',-.12,'o'),('frozen_prior',.12,'s')]:
 rr=[next(x for x in analysis if x['setting']==s and x['comparator']==comp and x['endpoint']=='delivery') for s in SET];m=np.array([x['difference'] for x in rr])*100;ci=np.array([x['ci95'] for x in rr])*100;y=np.arange(5)+offset;ax.errorbar(m,y,xerr=np.array([m-ci[:,0],ci[:,1]-m]),fmt=marker,color=C[comp],ms=5,capsize=3,label=LABEL[comp],elinewidth=2)
ax.axvline(0,color='#65727d',ls='--',lw=1);ax.set_yticks(range(5),SL);ax.invert_yaxis();ax.set_xlabel('Censored passive minus comparator delivery (percentage points)');ax.grid(axis='x',color='#e7eaee',lw=.6);ax.legend(frameon=False,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.01));f.subplots_adjust(left=.27,right=.98,bottom=.22,top=.83);save(f,'fig4_delivery_effects')
# Fig 5 estimation plot retains fixture pairing and every comparison.
f,axs=plt.subplots(1,2,figsize=(7,3.9),gridspec_kw={'width_ratios':[1,1.3]});ax=axs[0]
a=np.array([next(r['delivery'] for r in rows if r['seed']==s and r['setting']=='blackhole' and r['arm']=='active_proof') for s in range(77001,77031)])*100;b=np.array([next(r['delivery'] for r in rows if r['seed']==s and r['setting']=='blackhole' and r['arm']=='censored_passive') for s in range(77001,77031)])*100
for i in range(30):ax.plot([0,1],[a[i],b[i]],color='#b7bfc5',lw=.8,alpha=.7)
ax.scatter(np.zeros(30),a,c=C['active_proof'],s=15,zorder=3);ax.scatter(np.ones(30),b,c=C['censored_passive'],s=15,zorder=3);ax.set_xticks([0,1],['Active\nproofs','Censored\npassive']);ax.set_ylabel('Delivery (%)');ax.set_title('(a) Paired fixtures',loc='left',pad=12);ax.grid(axis='y',alpha=.15)
ax=axs[1];comps=['active_proof','naive_passive','frozen_prior','capacity_mlp_censored']
for y,comp in enumerate(comps):
 z=next(x for x in analysis if x['setting']=='blackhole' and x['endpoint']=='delivery' and x['comparator']==comp);m=100*z['difference'];lo,hi=np.array(z['ci95'])*100;ax.errorbar(m,y,xerr=[[m-lo],[hi-m]],fmt='o',color=C[comp],capsize=3,ms=6,elinewidth=2)
ax.axvline(0,ls='--',color='#65727d',lw=1);ax.set_yticks(range(4),[LABEL[c] for c in comps]);ax.invert_yaxis();ax.set_xlabel('Delivery difference\n(percentage points)');ax.set_title('(b) Mean and 95% interval',loc='left',pad=12);ax.grid(axis='x',alpha=.15);f.subplots_adjust(left=.09,right=.98,bottom=.20,top=.85,wspace=.7);save(f,'fig5_blackhole_estimation')
# Fig 6 descriptive contrasts expose energy-denominator interpretation.
f,axs=plt.subplots(1,3,figsize=(7.2,4),sharey=True)
for ax,metric,scale,title,xlabel in zip(axs,['radio_energy_j','energy_per_delivered_byte','phy_tx_frames'],[1000,1000,1],['(a) Total radio energy','(b) Energy efficiency','(c) PHY transmissions'],['Difference (mJ)','Difference (mJ/byte)','Difference (frames)']):
 z=[next(x for x in audit['contrasts'] if x['setting']==s and x['metric']==metric) for s in SET];m=np.array([x['difference'] for x in z])*scale;ci=np.array([x['ci95'] for x in z])*scale;ax.errorbar(m,np.arange(5),xerr=[m-ci[:,0],ci[:,1]-m],fmt='o',color=C['censored_passive'],capsize=3,ms=4,elinewidth=2);ax.axvline(0,color='#65727d',ls='--',lw=1);ax.set_title(title,loc='left',fontsize=9,pad=14);ax.set_xlabel(xlabel);ax.grid(axis='x',alpha=.15);ax.locator_params(axis='x',nbins=3)
axs[0].set_yticks(range(5),SL);axs[0].invert_yaxis();f.suptitle('Censored passive minus active proofs',fontsize=9,y=.98);f.subplots_adjust(left=.23,right=.98,bottom=.22,top=.82,wspace=.35);save(f,'fig6_energy_attribution')
(OUT/'figure_provenance.json').write_text(json.dumps({'inputs':['outputs/ns3_censored/summary.json','outputs/ns3_censored/paired_analysis.json','outputs/ns3_censored/implementation_audit.json'],'style':'Vector schematics and paired estimation plots; no generated or smoothed observations','confidence_intervals':'Unadjusted paired t intervals across 30 fixtures; inferential decisions retain original 60-test Holm family','figure3':'PRISMA-inspired experimental accounting layout; not a systematic-review selection diagram','captions':['Architecture and state boundaries','Censored feedback flow','Frozen evaluation flow','Delivery effects across settings','Blackhole paired estimates','Radio energy attribution']},indent=2));print(OUT)

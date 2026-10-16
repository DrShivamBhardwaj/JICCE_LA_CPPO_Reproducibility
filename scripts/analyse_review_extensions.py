"""Post-review diagnostics from executed runs, never synthetic trajectories."""
from pathlib import Path
import json,hashlib,gzip
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'outputs/review_extensions';O.mkdir(exist_ok=True);F=R/'publication/array/review_figures';F.mkdir(exist_ok=True)
long=[];sens=[];inputs={}
for root,target in [('review_long_horizon',long),('review_sensitivity',sens)]:
 for p in sorted((R/'outputs'/root).glob('*/summary_*.json')):
  inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();rows=json.loads(p.read_text());pr=json.loads((p.parent/'protocol.json').read_text())
  for row in rows:
   if root=='review_sensitivity':row.update(weight_index=pr['weight_index'],factor=pr['factor'])
   target.append(row)
assert len(long)==18 and len(sens)==33,(len(long),len(sens))
# Reconcile summaries with compressed final records for every stress/sensitivity run.
for root,target in [('review_long_horizon',long),('review_sensitivity',sens)]:
 count=0
 for p in sorted((R/'outputs'/root).glob('*/trace_*.jsonl.gz')):
  finals=[]
  with gzip.open(p,'rt') as stream:
   for line in stream:
    row=json.loads(line)
    if row['type']=='final':finals.append(row)
  summary=json.loads(next(p.parent.glob('summary_*.json')).read_text())
  for row in finals:
   saved=next(x for x in summary if all(x[k]==row[k] for k in ['seed','arm','setting']))
   assert all(row[k]==v for k,v in saved.items());count+=1
 assert count==len(target),(root,count)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
C={'active_proof':'#CA6940','censored_passive':'#007E87','frozen_prior':'#68758A'};labels={'active_proof':'Active proofs','censored_passive':'Censored passive','frozen_prior':'Frozen prior'}
def save(fig,name):
 for ext in ['png','pdf','svg']:fig.savefig(F/f'{name}.{ext}',dpi=600,bbox_inches='tight')
 plt.close(fig)
f,axes=plt.subplots(1,3,figsize=(10,3.5))
for arm in C:
 runs=[r for r in long if r['arm']==arm and r['duration_s']==300]
 for r in runs:
  samples=r['samples'];t=[v['time'] for v in samples]
  axes[0].step(t,[v['delivered'] for v in samples],where='post',color=C[arm],alpha=.6,lw=2)
  axes[1].plot(t,[v['debt_max'] for v in samples],color=C[arm],alpha=.6,lw=2)
  axes[2].plot(t,[v['watches'] for v in samples],color=C[arm],alpha=.6,lw=2)
 axes[0].plot([],[],color=C[arm],label=labels[arm],lw=2)
for ax,title,y in zip(axes,['(a) Delivery stops early','(b) Source debt accumulates','(c) Watch records remain'],['Delivered packets (count)','Maximum delay debt (dimensionless)','Retained watches (count)']):
 ax.set(xlabel='Elapsed time (s)',ylabel=y,title=title);ax.grid(alpha=.2)
axes[0].legend(fontsize=8);f.tight_layout();save(f,'fig9_long_horizon')
base={r['seed']:r for r in sens if r['weight_index']==-1};effects=[]
for i,name in enumerate(['Progress','MAC success','Energy','Risk','Queue']):
 for factor in [.8,1.2]:
  a=sorted([r for r in sens if r['weight_index']==i and r['factor']==factor],key=lambda r:r['seed']);delta=[100*(r['delivery']-base[r['seed']]['delivery']) for r in a]
  effects.append(dict(weight=name,factor=factor,paired_delivery_points=delta,mean=float(np.mean(delta)),range=[min(delta),max(delta)]))
f,ax=plt.subplots(figsize=(8,4.4))
for j,r in enumerate(effects):
 vals=r['paired_delivery_points'];ax.scatter(vals,np.array([j-.12,j,j+.12]),s=28,color='#007E87');ax.plot(r['range'],[j,j],color='#007E87',lw=2);ax.scatter(r['mean'],j,marker='D',color='#CA6940',s=40,zorder=3)
ax.axvline(0,ls='--',color='gray');ax.set(yticks=range(10),yticklabels=[f"{r['weight']} × {r['factor']:g}" for r in effects],xlim=(-1,1),xlabel='Delivery difference from unchanged weights (percentage points)',title='One-at-a-time preselection sensitivity · three paired fixtures');ax.invert_yaxis();ax.grid(axis='x',alpha=.2);f.text(.5,.005,'Dots: individual fixtures · diamonds: means · lines: observed ranges, not confidence intervals',ha='center',fontsize=8);f.tight_layout(rect=(0,.04,1,1));save(f,'fig10_weight_sensitivity')
groups=[]
for duration in [60,300]:
 for arm in C:
  a=[r for r in long if r['duration_s']==duration and r['arm']==arm];assert len(a)==3
  groups.append(dict(duration_s=duration,arm=arm,n=3,packets_per_run=a[0]['packets'],delivery_mean_percent=float(np.mean([100*r['delivery'] for r in a])),critical_failure_mean_percent=float(np.mean([100*r['critical_violation'] for r in a])),source_debt_max=max(r['terminal_source_debt_max'] for r in a),handle_exhaustions=sum(r['handle_exhaustions'] for r in a),retained_watch_max=max(r['peak_watches'] for r in a)))
report=dict(status='passed',long_runs=18,sensitivity_runs=33,fixtures_per_extension=3,source_inputs=inputs,long_groups=groups,sensitivity_effects=effects,math=json.loads((R/'outputs/review_math/audit.json').read_text()),limitations=['Post-review exploratory runs, not added confirmatory hypotheses.','Always-listening radio continues callbacks after routing energy gate closes; cumulative energy is not physically battery-limited.','1-second pending-map samples can miss queue transients; zero handle-exhaustion events do not prove zero MAC queue drops.','No duty-cycled MAC or clock-drift experiment; no embedded policy/crypto feasibility claim.'])
(O/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','long_runs','sensitivity_runs','long_groups','sensitivity_effects']},indent=2))

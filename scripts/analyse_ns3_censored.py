"""Frozen contrasts and all-required decision gate for passive redesign."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import t,ttest_1samp
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'outputs/ns3_censored';rows=[]
import gzip
for path in sorted(out.glob('trace_*.gz')):
 rr=[json.loads(l) for l in gzip.open(path,'rt') if '"type":"final"' in l];assert len(rr)==25,(path,len(rr));rows.extend({k:v for k,v in x.items() if k not in ['type','telemetry']} for x in rr)
assert len(rows)==750 and len({(x['seed'],x['setting'],x['arm']) for x in rows})==750
(out/'summary.json').write_text(json.dumps(rows,indent=2));protocol=json.loads((ROOT/'configs/ns3_censored_protocol.json').read_text());results=[]
for setting in protocol['settings']:
 for comparator in protocol['arms'][1:]:
  for endpoint in ['delivery','critical_violation','energy_per_delivered_byte']:
   aa=[];bb=[]
   for seed in range(77001,77031):
    rr={r['arm']:r for r in rows if r['seed']==seed and r['setting']==setting['name']};aa.append(rr['censored_passive'][endpoint]);bb.append(rr[comparator][endpoint])
   if any(x is None for x in aa+bb):results.append(dict(setting=setting['name'],comparator=comparator,endpoint=endpoint,n=30,status='undefined: zero delivered bytes',p=1.,holm_p=1.));continue
   a=np.array(aa);b=np.array(bb);d=a-b;mu=float(d.mean());se=float(d.std(ddof=1)/np.sqrt(30));half=float(t.ppf(.975,29)*se);p=float(ttest_1samp(d,0).pvalue) if d.std()>0 else (1. if mu==0 else 0.)
   row=dict(setting=setting['name'],comparator=comparator,endpoint=endpoint,n=30,censored_mean=float(a.mean()),comparator_mean=float(b.mean()),difference=mu,ci95=[mu-half,mu+half],lower_one_sided95=mu-float(t.ppf(.95,29))*se,upper_one_sided95=mu+float(t.ppf(.95,29))*se,p=p)
   if endpoint=='energy_per_delivered_byte':
    z=np.log(a/b);row['geometric_ratio']=float(np.exp(z.mean()));row['geometric_upper_one_sided95']=float(np.exp(z.mean()+t.ppf(.95,29)*z.std(ddof=1)/np.sqrt(30)))
   results.append(row)
prev=0
for rank,i in enumerate(sorted(range(60),key=lambda i:results[i]['p'])):prev=max(prev,min(1,results[i]['p']*(60-rank)));results[i]['holm_p']=prev
(out/'paired_analysis.json').write_text(json.dumps(results,indent=2))
def get(c,e):return next(x for x in results if x['setting']=='blackhole' and x['comparator']==c and x['endpoint']==e)
active=get('active_proof','delivery');delivery=get('frozen_prior','delivery');critical=get('frozen_prior','critical_violation');energy=get('frozen_prior','energy_per_delivered_byte')
checks=dict(active_blackhole_delivery_gain=active.get('difference',0)>0 and active['holm_p']<.05,frozen_delivery_noninferiority=delivery.get('lower_one_sided95',-1)>-.01,frozen_critical_noninferiority=critical.get('upper_one_sided95',1)<.01,frozen_energy_noninferiority=energy.get('geometric_upper_one_sided95',float('inf'))<1.02)
(out/'decision.json').write_text(json.dumps(dict(pass_all=all(checks.values()),checks=checks,scope='incremental mechanism gate; not original absolute QoS budgets, architecture superiority or deployment validation'),indent=2));print(json.dumps(checks,indent=2))

"""Exploratory paired fixture estimates; no endpoint or setting selection."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import t,ttest_1samp
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'outputs/ns3_multihop';rows=json.loads((out/'summary.json').read_text());results=[]
for attack in [False,True]:
 for endpoint in ['delivery','critical_violation_rate']:
  diff=[];values={a:[] for a in ['attention','capacity_mlp']}
  for seed in range(75001,75031):
   rr={r['arm']:r for r in rows if r['seed']==seed and r['attack']==attack}
   for arm,r in rr.items():values[arm].append(r['delivery'] if endpoint=='delivery' else r['critical_violations']/r['critical_packets'])
  d=np.array(values['attention'])-np.array(values['capacity_mlp']);mean=float(d.mean());half=float(t.ppf(.975,29)*d.std(ddof=1)/np.sqrt(30));p=float(ttest_1samp(d,0).pvalue) if d.std()>0 else 1.
  results.append(dict(attack=attack,endpoint=endpoint,n=30,attention_mean=float(np.mean(values['attention'])),capacity_mlp_mean=float(np.mean(values['capacity_mlp'])),paired_difference=mean,ci95=[mean-half,mean+half],p=p))
order=sorted(range(4),key=lambda i:results[i]['p']);prev=0
for rank,i in enumerate(order):prev=max(prev,min(1,results[i]['p']*(4-rank)));results[i]['holm_p']=prev
(out/'paired_analysis.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

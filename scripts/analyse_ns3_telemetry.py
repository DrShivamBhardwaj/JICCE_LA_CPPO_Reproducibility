"""One Holm family for all prespecified simulator-transfer comparisons."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import t,ttest_1samp
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'outputs/ns3_telemetry';rows=json.loads((out/'summary.json').read_text());protocol=json.loads((out/'protocol.json').read_text());results=[]
assert len(rows)==600
for setting in protocol['settings']:
 for comparator in protocol['arms'][1:]:
  for endpoint in ['delivery','critical_violation','energy_per_delivered_byte']:
   a=[];b=[]
   for seed in range(76001,76031):
    rr={r['arm']:r for r in rows if r['seed']==seed and r['setting']==setting['name']};a.append(rr['attention'][endpoint]);b.append(rr[comparator][endpoint])
   if any(x is None for x in a+b):
    results.append(dict(setting=setting['name'],comparator=comparator,endpoint=endpoint,n=30,status='undefined because a run delivered zero bytes',p=1.,holm_p=1.));continue
   d=np.array(a)-np.array(b);mu=float(d.mean());half=float(t.ppf(.975,29)*d.std(ddof=1)/np.sqrt(30));p=float(ttest_1samp(d,0).pvalue) if d.std()>0 else (1. if mu==0 else 0.)
   results.append(dict(setting=setting['name'],comparator=comparator,endpoint=endpoint,n=30,attention_mean=float(np.mean(a)),comparator_mean=float(np.mean(b)),difference=mu,ci95=[mu-half,mu+half],p=p))
prev=0
for rank,i in enumerate(sorted(range(45),key=lambda i:results[i]['p'])):prev=max(prev,min(1,results[i]['p']*(45-rank)));results[i]['holm_p']=prev
(out/'paired_analysis.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

"""Exploratory paired effects from the frozen 180-run transfer protocol."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'outputs/auth_policy'
rows=json.loads((out/'summary.json').read_text());rng=np.random.default_rng(94001)
effects=[];means=[]
for setting in ['benign','selective_drop']:
 for arm in ['greedy','mlp','attention']:
  subset=[r for r in rows if r['setting']==setting and r['arm']==arm]
  means.append(dict(setting=setting,arm=arm,**{k:float(np.mean([r[k] for r in subset])) for k in ['delivery','verified_receipts','critical_violation','total_radio_j','energy_per_delivered_byte']}))
 for comparator in ['greedy','mlp']:
  for endpoint in ['delivery','critical_violation','total_radio_j','energy_per_delivered_byte']:
   def values(arm):return np.array([next(r[endpoint] for r in rows if r['seed']==s and r['setting']==setting and r['arm']==arm) for s in range(83001,83031)])
   delta=values('attention')-values(comparator);samples=np.mean(delta[rng.integers(0,30,(10000,30))],axis=1)
   effects.append(dict(setting=setting,comparator=comparator,endpoint=endpoint,difference=float(np.mean(delta)),ci95=np.quantile(samples,[.025,.975]).tolist(),n=30,interpretation='exploratory paired percentile bootstrap; no multiplicity-adjusted superiority test'))
(out/'analysis.json').write_text(json.dumps(dict(arm_means=means,effects=effects),indent=2))
for e in effects:
 if e['endpoint']=='delivery':print(e)

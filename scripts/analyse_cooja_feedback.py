"""Prespecified paired seed analysis; original manuscript statistical families unchanged."""
from pathlib import Path
import json,csv,hashlib,argparse,gzip
import numpy as np
from cooja_input_integrity import verify_run_inputs
r=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--experiment',type=Path,default=r/'outputs/cooja_feedback/primary_600');args=parser.parse_args();out=args.experiment;protocol=json.loads((out/'protocol.json').read_text());runs=json.loads((out/'runs.json').read_text());assert len(runs)==600
assert (out/'audit_complete.json').exists();reports=[]
for x in runs:
 folder=r/x['folder'];d=json.loads((folder/'audit.json').read_text());assert d['status']=='independent_audit_passed'
 assert d['config']=={k:x[k] for k in ['mode','proof','attack','timing']}
 raw=verify_run_inputs(folder,d,x)
 first=raw.decode().splitlines()[0]
 assert int(first.split(':',1)[1])==x['seed'],'Recorded simulator seed mismatch'
 d.update(seed=x['seed'],arm=x['arm'],attack=x['attack'],timing=x['timing']);reports.append(d)
assert len({(d['seed'],d['arm'],d['attack'],d['timing']) for d in reports})==600
rng_ci=np.random.default_rng(64001);rng_p=np.random.default_rng(64002)
def ci(x):
 x=np.asarray(x,float);draw=x[rng_ci.integers(0,len(x),(20000,len(x)))].mean(1);return np.quantile(draw,[.025,.975]).tolist()
def paired_p(x):
 x=np.asarray(x,float)
 if not np.any(x):return 1.
 signs=rng_p.choice(np.array([-1,1],np.int8),(100000,len(x)));sim=abs((signs*x).mean(1));return float((1+np.sum(sim>=abs(x.mean())-1e-14))/100001)
def holm(rows):
 order=sorted(range(len(rows)),key=lambda i:rows[i]['p_unadjusted']);previous=0.
 for k,i in enumerate(order):previous=max(previous,min(1.,rows[i]['p_unadjusted']*(len(rows)-k)));rows[i]['p_holm']=previous
endpoints=['delivery','critical_sink_deadline_failure','total_tx_state_s'];groups=[];contrasts=[]
for attack in protocol['attacks']:
 for timing in protocol['timings']:
  for arm in protocol['arms']:
   data=sorted((d for d in reports if (d['attack'],d['timing'],d['arm'])==(attack,timing,arm)),key=lambda x:x['seed']);assert len(data)==30
   g=dict(attack=attack,timing=timing,arm=arm,n=30)
   for endpoint in endpoints:
    values=[d[endpoint] for d in data];g[endpoint]=float(np.mean(values));g[endpoint+'_ci95']=ci(values)
   g.update(delivered=sum(d['delivered'] for d in data),offered=1800,source_receipts=sum(d['source_receipts'] for d in data),policy_decisions=sum(d['policy_decisions'] for d in data),proof_application_requests=sum(int(d['transmitted_application_frames'].get('4',0)) for d in data));groups.append(g)
for endpoint in endpoints:
 family=[]
 for attack in protocol['attacks']:
  for timing in protocol['timings']:
   base={d['seed']:d[endpoint] for d in reports if (d['attack'],d['timing'],d['arm'])==(attack,timing,'censored')}
   for arm in ['active','naive','frozen','censored_proof']:
    target={d['seed']:d[endpoint] for d in reports if (d['attack'],d['timing'],d['arm'])==(attack,timing,arm)};assert set(base)==set(target)==set(protocol['seeds']);diff=np.array([target[s]-base[s] for s in protocol['seeds']]);family.append(dict(endpoint=endpoint,attack=attack,timing=timing,arm=arm,baseline='censored',n_pairs=30,mean_difference=float(diff.mean()),ci95=ci(diff),p_unadjusted=paired_p(diff),family_size=16))
 holm(family);contrasts.extend(family)
exploratory=[]
rng_ci=np.random.default_rng(64003);rng_p=np.random.default_rng(64004)
for endpoint in endpoints:
 family=[]
 for attack in protocol['attacks']:
  for timing in protocol['timings']:
   baseline={d['seed']:d[endpoint] for d in reports if (d['attack'],d['timing'],d['arm'])==(attack,timing,'censored_proof')}
   active={d['seed']:d[endpoint] for d in reports if (d['attack'],d['timing'],d['arm'])==(attack,timing,'active')}
   diff=np.array([active[s]-baseline[s] for s in protocol['seeds']]);family.append(dict(endpoint=endpoint,attack=attack,timing=timing,arm='active',baseline='censored_proof',n_pairs=30,mean_difference=float(diff.mean()),ci95=ci(diff),p_unadjusted=paired_p(diff),family_size=4,classification='exploratory_postfreeze'))
 holm(family);exploratory.extend(family)
result=dict(status='passed_paired_seed_analysis',runs=600,independent_seeds=30,offered_packets=sum(d['offered'] for d in reports),groups=groups,contrasts=contrasts,exploratory_matched_proof_contrasts=exploratory,primary_endpoint='delivery',secondary_families=['critical_sink_deadline_failure','total_tx_state_s'],ci_scope='Pointwise paired bootstrap intervals over independent seeds; not simultaneous intervals',p_scope='Two-sided paired sign-flip randomization; 100000 Monte Carlo draws plus-one correction; Holm within each declared 16-contrast endpoint family',physical_energy_measured=False,max_feature_error=max(d['max_feature_error'] for d in reports),max_logit_error=max(d['max_logit_error'] for d in reports),policy_decisions=sum(d['policy_decisions'] for d in reports),multiple_choices=sum(d['multiple_choices'] for d in reports),feedback_events_replayed=sum(d['feedback_events_replayed'] for d in reports),scope=protocol['scope'],protocol_sha256=hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest())
(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for name,items in [('groups',groups),('paired_contrasts',contrasts),('exploratory_matched_proof',exploratory)]:
 with (out/(name+'.csv')).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
print(json.dumps({k:v for k,v in result.items() if k not in ['groups','contrasts','exploratory_matched_proof_contrasts']},indent=2))

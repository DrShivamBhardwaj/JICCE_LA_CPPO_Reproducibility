"""Independent, geometry-clustered generalization analysis. Do not pool with remediation v1."""
from pathlib import Path
import json,hashlib,numpy as np
D=Path(__file__).resolve().parent
O=D.parents[1]/'outputs/generalization_v2'
def effects(v):
    c0,c1,n0,n1=(v[x] for x in ['censored','censored_proof','negative','negative_proof'])
    return {'negative_main':((n0-c0)+(n1-c1))/2,
            'proof_main':((c1-c0)+(n1-n0))/2,
            'interaction':(n1-n0)-(c1-c0)}
def main():
    p=json.loads((D/'protocol.json').read_text())
    done=json.loads((O/'execution_complete.json').read_text())
    if done['cases']!=1920 or p['expected_runs']!=1920:raise ValueError('incomplete study')
    groups=[]
    for c in p['cases']:
        a=json.loads((O/'runs'/c['case_id']/'audit.json').read_text())
        if a['status']!='independent_audit_passed' or a['antecedent_provenance']['status']!='passed_antecedent_event_checks':raise ValueError('failed case '+c['case_id'])
        m=a['metrics']
        groups.append(c|dict(post_delivery=m['post_attack_delivered']/m['post_attack_offered'],
                             critical_failure=m['critical_failure'],tx_seconds=a['total_tx_state_s']))
    rng=np.random.default_rng(2026102902)
    result=[]
    for endpoint in ['post_delivery','critical_failure','tx_seconds']:
        family=[]
        for timing in (0,1):
            blockvalues=[]
            for block in range(24):
                data=[x for x in groups if x['block']==block and x['timing']==timing]
                v={arm:float(np.mean([x[endpoint] for x in data if x['arm']==arm])) for arm in ['censored','censored_proof','negative','negative_proof']}
                blockvalues.append(effects(v))
            for contrast in ['negative_main','proof_main','interaction']:
                x=np.array([v[contrast] for v in blockvalues])
                bs=np.mean(x[rng.integers(0,24,(20000,24))],axis=1)
                signs=rng.choice((-1,1),size=(50000,24))
                pv=(1+int(np.sum(np.abs(np.mean(signs*x,axis=1))>=abs(np.mean(x))-1e-14)))/50001
                family.append(dict(endpoint=endpoint,timing=timing,contrast=contrast,blocks=24,
                   mean_difference=float(np.mean(x)),ci95=np.quantile(bs,[.025,.975]).tolist(),
                   p_unadjusted=float(pv),block_differences=x.tolist()))
        prior=0
        for j,c in enumerate(sorted(family,key=lambda r:r['p_unadjusted'])):
            prior=max(prior,min(1.,c['p_unadjusted']*(6-j)));c['p_holm']=prior
        result.extend(family)
    out={'status':'completed_generalization_v2','runs':len(groups),'independent_geometry_blocks':24,
         'inference_scope':p['analysis_plan'],'contrasts':result,
         'protocol_sha256':hashlib.sha256((D/'protocol.json').read_bytes()).hexdigest(),
         'physical_validation':False}
    (O/'analysis.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'runs':out['runs'],'blocks':24,
       'post_delivery_contrasts':[x for x in result if x['endpoint']=='post_delivery']},indent=2))
if __name__=='__main__':main()

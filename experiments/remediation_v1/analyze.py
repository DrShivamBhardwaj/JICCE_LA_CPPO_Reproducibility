"""Prespecified block-level factorial contrasts; packet counts are not replicates."""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;O=R/'outputs/remediation_v1'

def effects(values):
    c0,c1,n0,n1=(values[x] for x in ['censored','censored_proof','negative','negative_proof'])
    return {'negative_main':((n0-c0)+(n1-c1))/2,'proof_main':((c1-c0)+(n1-n0))/2,'interaction':(n1-n0)-(c1-c0)}

def main():
    p=json.loads((D/'protocol.json').read_text());done=json.loads((O/'execution_complete.json').read_text())
    if done['cases']!=p['expected_runs']:raise ValueError('incomplete study')
    reports={};groups=[]
    for c in p['cases']:
        folder=O/'runs'/c['case_id'];a=json.loads((folder/'audit.json').read_text())
        if a['status']!='independent_audit_passed' or a['antecedent_provenance']['status']!='passed_antecedent_event_checks':raise ValueError('audit acceptance')
        reports[c['case_id']]=a
        m=a['metrics'];groups.append(c|dict(delivery=a['delivery'],post_delivery=m['post_attack_delivered']/m['post_attack_offered'],critical_failure=m['critical_failure'],tx_seconds=a['total_tx_state_s'],critical_undelivered=m['critical_undelivered'],critical_delivered_late=m['critical_delivered_late'],post_losses=m['post_attack_losses'],source_switches=m['source_relay_switches'],first_safe_choice_packet_offset=m['first_safe_choice_packet_offset']))
    rows=[];rng=np.random.default_rng(951019);signs=np.array(list(itertools.product([-1,1],repeat=12)),dtype=np.int8)
    for endpoint in ['post_delivery','critical_failure','tx_seconds']:
        family=[]
        for timing in [0,1]:
            block_effects=[]
            for block in range(12):
                data=[x for x in groups if x['block']==block and x['timing']==timing and x['physical_attacker']!=0]
                values={arm:float(np.mean([x[endpoint] for x in data if x['arm']==arm])) for arm in ['censored','censored_proof','negative','negative_proof']}
                block_effects.append(effects(values))
            for contrast in ['negative_main','proof_main','interaction']:
                x=np.array([b[contrast] for b in block_effects]);draw=x[rng.integers(0,12,(20000,12))].mean(1);pv=float(np.mean(abs((signs*x).mean(1))>=abs(x.mean())-1e-14));family.append(dict(endpoint=endpoint,timing=timing,contrast=contrast,blocks=12,mean_difference=float(x.mean()),ci95=np.quantile(draw,[.025,.975]).tolist(),p_unadjusted=pv,block_differences=x.tolist()))
        prior=0
        for j,x in enumerate(sorted(family,key=lambda x:x['p_unadjusted'])):prior=max(prior,min(1.,x['p_unadjusted']*(6-j)));x['p_holm']=prior
        rows.extend(family)
    result={'status':'completed_block_factorial_analysis','classification':p['classification'],'runs':len(groups),'independent_geometry_blocks':12,'primary_endpoint':'post_delivery','contrasts':rows,'inference_scope':p['statistical_plan'],'physical_validation':False,'protocol_sha256':hashlib.sha256((D/'protocol.json').read_bytes()).hexdigest()}
    (O/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(O/'run_endpoints.json').write_text(json.dumps(groups,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

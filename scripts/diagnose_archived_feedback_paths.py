"""Exploratory measured-logit and effective-count trajectories from retained captures."""
from pathlib import Path
import sys,json,struct,math,csv,io,gzip,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'experiments/remediation_v1'))
from trace_tools import read_events

def main():
    out=R/'outputs/remediation_v1/archive_diagnostics';primary=R/'outputs/cooja_feedback/primary_600';runs=json.loads((primary/'runs.json').read_text());paired={};stream=io.StringIO();w=csv.writer(stream);w.writerow(['seed','attack','timing','arm','node','peer','pid','now_ms','operation','alpha','beta','risk_heuristic','risk_upper_heuristic']);count=0
    for run in runs:
        raw,events=read_events(R/run['folder']);saved=json.loads((R/run['folder']/'audit.json').read_text());assert hashlib.sha256(raw).hexdigest()==saved['log_sha256']
        if run['arm'] in ('censored','frozen'):paired[(run['seed'],run['attack'],run['timing'],run['arm'])]={(v['_node'],v['pid']):v for v in events if v['event']=='local_decision'}
        for v in events:
            if v['event']!='feedback':continue
            alpha,beta=v['a'],v['b'];risk=.75*beta/(alpha+beta);std=math.sqrt(alpha*beta/((alpha+beta)**2*(alpha+beta+1)))
            w.writerow([run[k] for k in ['seed','attack','timing','arm']]+[v['_node'],v['peer'],v['pid'],v['now_ms'],v['op'],alpha,beta,risk,min(1,risk+1.645*.75*std)]);count+=1
    result=[]
    for (seed,attack,timing,arm),a in paired.items():
        if arm!='censored':continue
        b=paired[(seed,attack,timing,'frozen')];changed=0;maximum=0.;margins=[]
        for key in a.keys()&b.keys():
            x,y=a[key],b[key];assert x['ids']==y['ids'];n=len(x['ids']);lx=np.array(struct.unpack('!8f',bytes.fromhex(x['logits_hex'])))[:n];ly=np.array(struct.unpack('!8f',bytes.fromhex(y['logits_hex'])))[:n];delta=float(np.max(abs(lx-ly)));changed+=delta>0;maximum=max(maximum,delta)
            if n>1:margins.append(float(np.sort(lx)[-1]-np.sort(lx)[-2]))
        result.append(dict(seed=seed,attack=attack,timing=timing,matched=len(a.keys()&b.keys()),logits_differ=changed,max_valid_logit_difference=maximum,minimum_observed_multichoice_margin=min(margins) if margins else None))
    (out/'effective_count_trajectories.csv.gz').write_bytes(gzip.compress(stream.getvalue().encode(),mtime=0));(out/'natural_logit_pairs.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={'classification':'Exploratory paired recorded-logit analysis; no intervention or new radio run','feedback_rows':count,'matched_decisions':sum(x['matched'] for x in result),'logits_differ':sum(x['logits_differ'] for x in result),'max_valid_logit_difference':max(x['max_valid_logit_difference'] for x in result),'risk_columns':'Implemented heuristic with .75 scaling and 1.645 multiplier; not calibrated uncertainty','physical_validation':False}
    (out/'path_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

"""Exploratory offline diagnostics of the archived 600 runs, not new radio results."""
from pathlib import Path
import argparse,json,collections,struct,ctypes,subprocess,csv,hashlib,sys
import numpy as np
from trace_tools import read_events,causal_audit,run_metrics
R=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    primary=R/'outputs/cooja_feedback/primary_600';runs=json.loads((primary/'runs.json').read_text());rows=[];pairs={};samples=collections.defaultdict(list);audits=[]
    for i,run in enumerate(runs):
        folder=R/run['folder'];raw,events=read_events(folder);saved=json.loads((folder/'audit.json').read_text())
        if hashlib.sha256(raw).hexdigest()!=saved['log_sha256']:raise ValueError('stale archive audit')
        provenance=causal_audit(events);audits.append(dict(folder=run['folder'],log_sha256=hashlib.sha256(raw).hexdigest(),**provenance))
        metrics=run_metrics(events);rows.append({k:run[k] for k in ['seed','attack','timing','arm']}|metrics)
        decisions={(v['_node'],v['pid']):v for v in events if v['event']=='local_decision'}
        if run['arm'] in ('censored','frozen'):pairs[(run['seed'],run['attack'],run['timing'],run['arm'])]=decisions
        if run['arm']=='censored':
            for v in decisions.values():
                if v['_node']==0 and len(v['ids'])>1:samples[(run['attack'],run['timing'])].append((run['seed'],v))
        if i%100==0:print('Archived runs checked',i,flush=True)
    paired=[]
    for seed,attack,timing,arm in pairs:
        if arm!='censored':continue
        a=pairs[(seed,attack,timing,'censored')];b=pairs[(seed,attack,timing,'frozen')];keys=set(a)&set(b);risk_changed=0;other_changed=0;action_changed=0;ranking_changed=0
        for key in keys:
            x,y=a[key],b[key];ox=np.array(struct.unpack('!93f',bytes.fromhex(x['obs_hex'])));oy=np.array(struct.unpack('!93f',bytes.fromhex(y['obs_hex'])));risk=[13+10*j+k for j in range(8) for k in (6,7)];other=np.ones(93,bool);other[risk]=False
            risk_changed+=not np.array_equal(ox[risk],oy[risk]);other_changed+=not np.array_equal(ox[other],oy[other]);action_changed+=x['peer']!=y['peer'];ranking_changed+=x['ids']!=y['ids']
        paired.append(dict(seed=seed,attack=attack,timing=timing,matched_decisions=len(keys),unmatched_censored=len(set(a)-keys),unmatched_frozen=len(set(b)-keys),risk_coordinates_differ=risk_changed,other_coordinates_differ=other_changed,selected_peer_differs=action_changed,candidate_order_differs=ranking_changed))
    # Evaluate the retained compiled Q22 actor; no torch or retraining required.
    build=out/'native';build.mkdir(exist_ok=True);source=build/'actor_eval.c';source.write_text('#include "actor.h"\nint evaluate(const float*x,const unsigned char*m,float*y){return actor(x,m,y);}\n');library=build/'actor.so'
    subprocess.run(['cc','-O2','-shared','-fPIC','-I'+str(R/'hardware/cc2538_q22'),str(source),'-o',str(library)],check=True)
    lib=ctypes.CDLL(str(library.resolve()));f=lib.evaluate;f.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_ubyte),ctypes.POINTER(ctypes.c_float)]
    def evaluate(obs,mask):
        x=np.asarray(obs,np.float32);m=np.asarray(mask,np.uint8);y=np.zeros(8,np.float32);selected=f(x.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),m.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),y.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        if selected<0:raise ValueError('invalid actor intervention')
        return selected,y
    interventions=[]
    for (attack,timing),available in sorted(samples.items()):
        available.sort(key=lambda x:(x[0],x[1]['pid']));indices=np.linspace(0,len(available)-1,min(120,len(available)),dtype=int)
        for index in indices:
            seed,v=available[index];obs=np.array(struct.unpack('!93f',bytes.fromhex(v['obs_hex'])),np.float32);mask=np.zeros(8,np.uint8);mask[:len(v['ids'])]=1;selected,base=evaluate(obs,mask)
            if v['ids'][selected]!=v['peer']:raise ValueError('native baseline action mismatch')
            for candidate in range(len(v['ids'])):
                for alpha,beta in [(1,1),(5,1),(20,1),(1,5),(1,20)]:
                    counter=obs.copy();risk=.75*beta/(alpha+beta);std=(alpha*beta/((alpha+beta)**2*(alpha+beta+1)))**.5;counter[13+10*candidate+6]=risk;counter[13+10*candidate+7]=min(1,risk+1.645*.75*std);new,logit=evaluate(counter,mask)
                    interventions.append(dict(seed=seed,attack=attack,timing=timing,pid=v['pid'],candidate=v['ids'][candidate],alpha=alpha,beta=beta,action_changed=new!=selected,max_logit_change=float(np.max(abs(logit[mask.astype(bool)]-base[mask.astype(bool)])))))
    groups=[]
    for attack in (0,1):
        for timing in (0,1):
            for arm in ['censored','frozen','naive','active','censored_proof']:
                data=[x for x in rows if (x['attack'],x['timing'],x['arm'])==(attack,timing,arm)]
                groups.append(dict(attack=attack,timing=timing,arm=arm,runs=len(data),critical_offered=sum(x['critical_offered'] for x in data),critical_undelivered=sum(x['critical_undelivered'] for x in data),critical_delivered_late=sum(x['critical_delivered_late'] for x in data),sink_delay_ms_median=float(np.median([v for x in data for v in x['sink_delay_ms']])),source_signed_receipt_delay_ms_median=float(np.median([v for x in data for v in x['source_signed_receipt_delay_ms']]))))
    for name,data in [('run_diagnostics',rows),('paired_decisions',paired),('risk_interventions',interventions),('deadline_groups',groups)]:
        (out/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    (out/'causal_provenance.json').write_text(json.dumps(audits,indent=2)+'\n')
    summary=dict(classification='exploratory post-hoc archive diagnostics; interventions are offline, not closed-loop performance',archived_runs=len(rows),provenance_passed=len(audits),paired_runs=len(paired),matched_decisions=sum(x['matched_decisions'] for x in paired),action_disagreements=sum(x['selected_peer_differs'] for x in paired),risk_different_decisions=sum(x['risk_coordinates_differ'] for x in paired),other_different_decisions=sum(x['other_coordinates_differ'] for x in paired),candidate_order_disagreements=sum(x['candidate_order_differs'] for x in paired),offline_interventions=len(interventions),offline_action_changes=sum(x['action_changed'] for x in interventions),max_offline_logit_change=max(x['max_logit_change'] for x in interventions),deadline_groups=groups,physical_validation=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

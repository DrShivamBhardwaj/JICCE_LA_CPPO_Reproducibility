"""Descriptive secondary diagnostics; no new hypothesis tests or threshold selection."""
from pathlib import Path
import sys,json,collections,csv,gzip,io,math
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'experiments/remediation_v1'))
from trace_tools import read_events
from verify_remediation_archive import verify_dataset

def main():
    out=R/'outputs/remediation_v1';verify_dataset(out)
    cases=json.loads((R/'experiments/remediation_v1/protocol.json').read_text())['cases'];rows=[];trajectory=io.StringIO();w=csv.writer(trajectory);w.writerow(['case_id','node','peer','pid','now_ms','operation','alpha','beta','risk_heuristic','risk_upper_heuristic','seen','credited','expected'])
    losses=io.StringIO();loss_writer=csv.writer(losses);loss_writer.writerow(['case_id','pid','post_onset','sink_delivered','sink_delay_ms','signed_receipt_delay_ms','cumulative_post_onset_losses'])
    for c in cases:
        f=out/'runs'/c['case_id'];a=json.loads((f/'audit.json').read_text());m=a['metrics'];_,events=read_events(f)
        offered={v['pid']:v['now_ms'] for v in events if v['event']=='cooja_offer'};sink={v['pid']:v['now_ms'] for v in events if v['event']=='local_sink_delivery'};receipts={v['pid']:v['now_ms'] for v in events if v['event']=='local_receipt' and v['_node']==0};cumulative=0
        for pid,t in sorted(offered.items()):
            post_onset=pid>=c['onset'];cumulative+=post_onset and pid not in sink
            loss_writer.writerow([c['case_id'],pid,int(post_onset),int(pid in sink),sink[pid]-t if pid in sink else '',receipts[pid]-t if pid in receipts else '',cumulative])
        choices=[v for v in events if v['event']=='local_decision' and v['_node']==0]
        pre=[v for v in choices if v['pid']<c['onset']];post=[v for v in choices if v['pid']>=c['onset']]
        previously_attacker=bool(pre and pre[-1]['peer']==c['attacker'])
        post_switches=sum(x['peer']!=y['peer'] for x,y in zip(post,post[1:]))
        proofs=[bytes.fromhex(v['wire']) for v in events if v['event']=='local_tx' and bytes.fromhex(v['wire'])[1]==4]
        feedback=collections.Counter()
        for v in events:
            if v['event']!='feedback':continue
            feedback[v['op']+(':'+v['kind'] if v['kind'] else '')]+=1
            alpha,beta=v['a'],v['b'];risk=.75*beta/(alpha+beta);std=math.sqrt(alpha*beta/((alpha+beta)**2*(alpha+beta+1)))
            w.writerow([c['case_id'],v['_node'],v['peer'],v['pid'],v['now_ms'],v['op'],alpha,beta,risk,min(1,risk+1.645*.75*std),v['seen'],v['credited'],v['expected']])
        rows.append({k:c[k] for k in ['case_id','block','checkpoint','onset','rx_probability','timing','arm','physical_attacker','seed']}|dict(last_pre_onset_choice_attacker=previously_attacker,post_onset_relay_switches=post_switches,post_delivery=m['post_attack_delivered']/m['post_attack_offered'],post_losses=m['post_attack_losses'],relay_switches=m['source_relay_switches'],source_attacker_choices_post=m['source_attacker_choices_post'],sustained_start=m['sustained_safe_choice_start_offset'],sustained_confirmation_ms=m['sustained_safe_choice_confirmation_ms'],recovered_within_20=m['recovered_within_20_opportunities'],proof_frames=len(proofs),proof_wire_bytes=sum(map(len,proofs)),feedback_events=dict(feedback),critical_undelivered=m['critical_undelivered'],critical_delivered_late=m['critical_delivered_late']))
    groups=[]
    for timing in [0,1]:
        for arm in ['censored','censored_proof','negative','negative_proof','active_reference']:
            selected=[r for r in rows if r['timing']==timing and r['arm']==arm and r['physical_attacker']!=0];observed=[r for r in selected if r['sustained_start'] is not None]
            blockmean=lambda key:float(np.mean([np.mean([r[key] for r in selected if r['block']==b]) for b in range(12)]))
            groups.append(dict(timing=timing,arm=arm,attacked_runs=len(selected),right_censored=len(selected)-len(observed),recovered_within_20=sum(r['recovered_within_20'] for r in selected),last_pre_onset_choice_attacker=sum(r['last_pre_onset_choice_attacker'] for r in selected),recovered_within_20_previously_attacker=sum(r['recovered_within_20'] and r['last_pre_onset_choice_attacker'] for r in selected),conditional_median_start_opportunities=float(np.median([r['sustained_start'] for r in observed])) if observed else None,conditional_median_confirmation_ms=float(np.median([r['sustained_confirmation_ms'] for r in observed])) if observed else None,mean_post_delivery=blockmean('post_delivery'),mean_post_losses=blockmean('post_losses'),mean_proof_frames=blockmean('proof_frames'),mean_proof_wire_bytes=blockmean('proof_wire_bytes'),mean_relay_switches=blockmean('relay_switches'),mean_post_onset_relay_switches=blockmean('post_onset_relay_switches')))
    (out/'secondary_run_diagnostics.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'feedback_trajectories.csv.gz').write_bytes(gzip.compress(trajectory.getvalue().encode(),mtime=0))
    (out/'loss_and_latency_trajectories.csv.gz').write_bytes(gzip.compress(losses.getvalue().encode(),mtime=0))
    result={'classification':'Descriptive secondary aggregation; no additional significance tests, equivalence claim or threshold estimate','groups':groups,'experimental_unit':'geometry block for means; recovery tallies are descriptive counts of correlated run settings','recovery_warning':'The frozen three-safe-choice criterion includes routers already avoiding the attacker. Exposure-stratified counts and post-onset switch summaries are additional exploratory diagnostics, not proof of learning.','conditional_latency_warning':'Medians exclude right-censored runs and must be read with censoring counts, not as overall adaptation estimates','stale_field_note':'The inherited adaptation_scope string in raw audits describes first_safe_choice only. Sustained fields implement the separately specified three-choice criterion.','risk_warning':'Risk columns use the implemented .75 and 1.645 heuristic; not calibrated confidence limits.','physical_validation':False}
    (out/'secondary_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

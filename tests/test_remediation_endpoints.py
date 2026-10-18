from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments/remediation_v1'))
from trace_tools import run_metrics

def event(kind,pid,now,node=0,**extra):
    return dict(event=kind,pid=pid,now_ms=now,_node=node,_time_us=now*1000,**extra)

def test_delivery_loss_and_lateness_are_disjoint():
    events=[event('cooja_offer',i,i*300) for i in range(6)]
    events += [event('local_sink_delivery',0,100,node=3),event('local_sink_delivery',1,320,node=3),event('local_receipt',0,200)]
    x=run_metrics(events,onset=0,attacker=1)
    assert x['critical_offered']==2 and x['critical_undelivered']==1 and x['critical_delivered_late']==1
    assert x['critical_failure']==1 and x['sink_delay_ms']==[100,20] and x['source_signed_receipt_delay_ms']==[200]

def test_single_safe_choice_is_not_sustained_recovery():
    events=[event('cooja_offer',i,i*300) for i in range(6)]
    events += [event('local_decision',i,i*300,peer=peer) for i,peer in enumerate([2,1,2,2,2,1])]
    x=run_metrics(events,onset=0,attacker=1)
    assert x['first_safe_choice_packet_offset']==0
    assert x['sustained_safe_choice_start_offset']==2 and x['sustained_safe_choice_confirmation_ms']==1200
    assert x['recovered_within_20_opportunities']

def test_missing_choices_break_consecutive_recovery_and_censor():
    events=[event('cooja_offer',i,i*300) for i in range(6)]
    events += [event('local_decision',i,i*300,peer=2) for i in [0,2,4]]
    x=run_metrics(events,onset=0,attacker=1)
    assert x['first_safe_choice_observed'] and x['sustained_safe_choice_start_offset'] is None
    assert not x['recovered_within_20_opportunities']

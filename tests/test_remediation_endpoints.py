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


# Independent archive-integrity rejection tests use explicit synthetic unit fixtures.
import json,gzip,hashlib
import xml.etree.ElementTree as E
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_remediation_archive import verify_dataset

@pytest.fixture
def archive(tmp_path):
    case=dict(case_id='fixture',seed=7,mode=0,proof=0,attacker=1,timing=0,checkpoint=41001,rx_probability=1.,positions=[[0,0],[45,15],[45,-15],[90,0]])
    protocol={'expected_runs':1,'cases':[case],'source_sha256':{'outputs/jicce_validation/checkpoints/attention_41001.pt':'0'*64}}
    p=tmp_path/'protocol.json';p.write_text(json.dumps(protocol));sha=hashlib.sha256(p.read_bytes()).hexdigest();dataset=tmp_path/'dataset';f=dataset/'runs/fixture';f.mkdir(parents=True)
    (dataset/'analysis.json').write_text(json.dumps(dict(status='completed_block_factorial_analysis',runs=1,protocol_sha256=sha)))
    (dataset/'execution_complete.json').write_text(json.dumps(dict(cases=1,protocol_sha256=sha)))
    (f/'case.json').write_text(json.dumps(case));raw=b'Random seed: 7\nTEST OK\n';image=b'unit image'
    (f/'COOJA.testlog.gz').write_bytes(gzip.compress(raw));(f/'native_mote.so.gz').write_bytes(gzip.compress(image))
    audit=dict(status='independent_audit_passed',antecedent_provenance={'status':'passed_antecedent_event_checks'},log_sha256=hashlib.sha256(raw).hexdigest(),native_image_sha256=hashlib.sha256(image).hexdigest(),config={'mode':0,'proof':0,'attack':1,'timing':0},checkpoint_sha256='0'*64)
    (f/'audit.json').write_text(json.dumps(audit));root=E.Element('simconf');sim=E.SubElement(root,'simulation');E.SubElement(sim,'randomseed').text='7';medium=E.SubElement(sim,'radiomedium');E.SubElement(medium,'success_ratio_rx').text='1';mt=E.SubElement(sim,'motetype')
    for i,xy in enumerate(case['positions']):
        mote=E.SubElement(mt,'mote');c=E.SubElement(mote,'interface_config');E.SubElement(c,'pos',x=str(xy[0]),y=str(xy[1]));c=E.SubElement(mote,'interface_config');E.SubElement(c,'id').text=str(i+1)
    E.ElementTree(root).write(f/'simulation.csc');return dataset,p,f

def test_complete_archive_inputs_match(archive):
    dataset,p,_=archive;assert verify_dataset(dataset,p)['cases']==1

@pytest.mark.parametrize('mutation',['log','image','channel','missing_mote'])
def test_stale_or_mismatched_archive_rejected(archive,mutation):
    dataset,p,f=archive
    if mutation=='log':(f/'COOJA.testlog.gz').write_bytes(gzip.compress(b'changed capture'))
    elif mutation=='image':(f/'native_mote.so.gz').write_bytes(gzip.compress(b'changed image'))
    else:
        tree=E.parse(f/'simulation.csc')
        if mutation=='channel':tree.find('simulation/radiomedium/success_ratio_rx').text='.8'
        else:
            mt=tree.find('simulation/motetype');mt.remove(mt.findall('mote')[-1])
        tree.write(f/'simulation.csc')
    with pytest.raises(ValueError):verify_dataset(dataset,p)

from trace_tools import read_events,causal_audit
import copy

def test_received_replay_with_wrong_session_cannot_support_credit():
    root=Path(__file__).resolve().parents[1]
    events=copy.deepcopy(read_events(root/'outputs/cooja_feedback/geometry_corrected')[1])
    target=next(x for x in events if x['event']=='feedback' and x['op']=='evidence')
    kind=2 if target['kind']=='passive' else 3 if target['kind']=='receipt' else 4
    matches=[]
    for x in events:
        if x['event'] not in ('cooja_rx','cooja_passive'):continue
        wire=bytes.fromhex(x['wire'])
        if x['_node']==target['_node'] and x.get('peer')==target['peer'] and wire[1]==kind and int.from_bytes(wire[22:26],'big')==target['pid']:matches.append(x['wire'])
    assert matches
    for old in set(matches):
        wire=bytearray.fromhex(old);wire[26:34]=(int.from_bytes(wire[26:34],'big')+100).to_bytes(8,'big');new=wire.hex()
        for x in events:
            if x.get('wire')==old:x['wire']=new
    with pytest.raises(ValueError,match='unsupported or premature'):causal_audit(events)

def test_feedback_credit_for_another_packet_is_rejected():
    root=Path(__file__).resolve().parents[1]
    events=copy.deepcopy(read_events(root/'outputs/cooja_feedback/geometry_corrected')[1])
    target=next(x for x in events if x['event']=='feedback' and x['op']=='evidence');target['pid']=9999
    with pytest.raises(ValueError,match='unsupported or premature'):causal_audit(events)

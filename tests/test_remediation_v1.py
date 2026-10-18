from pathlib import Path
import sys,json,subprocess,copy,math
import pytest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'experiments/remediation_v1'))
from design import generate,ARMS
from prepare import project
from trace_tools import read_events,causal_audit

def test_balanced_design_and_radio_geometry():
    blocks,cases=generate();assert len(blocks)==12 and len(cases)==1440
    assert len({c['case_id'] for c in cases})==1440
    for c in cases:
        assert c['checkpoint'] in [41001,41002,41003]
        if c['physical_attacker']:assert c['attacker']==(c['physical_attacker'] if not c['permutation'] else 3-c['physical_attacker'])
        for relay in [1,2]:
            assert math.dist(c['positions'][0],c['positions'][relay])<50
            assert math.dist(c['positions'][3],c['positions'][relay])<50
    for block in blocks:
        subset=[c for c in cases if c['block']==block['block']]
        assert len(subset)==120
        for arm in ARMS:assert sum(c['arm']==arm for c in subset)==24

def test_compiled_matched_rules_have_same_late_positive_handling(tmp_path):
    _,cases=generate();weights=tmp_path/'weights.h';weights.write_text('/* fixture */')
    folder=tmp_path/'project';project(folder,cases[0],weights)
    inline=(folder/'local_feedback.h').read_text();ledger=(folder/'feedback_ledger.h').read_text()
    assert '(feedback_mode!=0&&feedback_mode!=2)||watches[i].acked!=1' in inline
    assert 'node_id==attack_node&&u32(body+2)>=attack_onset' in inline
    source=tmp_path/'test.c';source.write_text('''#include <stdio.h>
#include <stdint.h>
#include <string.h>
static unsigned node_id,feedback_mode;static uint32_t now;
#define milliseconds now
static float clip(float x,float a,float b){return x<a?a:x>b?b:x;}
#include "project/feedback_ledger.h"
int main(void){for(unsigned mode=0;mode<=2;mode+=2){feedback_mode=mode;memset(watches,0,sizeof watches);feedback_a[1]=feedback_b[1]=1;now=0;feedback_register(0,1,1,.9);now=10;feedback_ack(0,1);now=170;feedback_expire();now=180;feedback_evidence(1,1,1,"receipt");printf("RESULT %u %.3f %.3f\\n",mode,feedback_a[1],feedback_b[1]);}return 0;}
''')
    subprocess.run(['cc',str(source),'-o',str(tmp_path/'test')],check=True)
    out=subprocess.check_output([str(tmp_path/'test')],text=True)
    assert 'RESULT 0 1.900 1.000' in out and 'RESULT 2 1.900 1.900' in out

@pytest.fixture
def events():
    return read_events(R/'outputs/cooja_feedback/geometry_corrected')[1]

def test_antecedent_events_support_retained_fixture(events):
    assert causal_audit(events)['status']=='passed_antecedent_event_checks'

@pytest.mark.parametrize('mutation',['unsupported_evidence','false_ack','premature_processing'])
def test_false_antecedents_rejected(events,mutation):
    events=copy.deepcopy(events)
    if mutation=='unsupported_evidence':
        v=next(x for x in events if x['event']=='feedback' and x['op']=='evidence');v['kind']='forged'
    elif mutation=='false_ack':
        v=next(x for x in events if x['event']=='feedback' and x['op']=='ack');v['ok']=1-int(bool(v['ok']))
    else:
        for v in events:
            if v['event']=='cooja_rx' and bytes.fromhex(v['wire'])[1] in [2,3]:v['ready_ms']=1000000
    with pytest.raises(ValueError):causal_audit(events)

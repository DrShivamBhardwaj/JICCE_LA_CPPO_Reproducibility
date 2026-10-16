import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from wsn_sim.distributed_auth import *

def setup_nodes(capacity=128):
    secret=Ed25519PrivateKey.from_private_bytes(b'\x42'*32)
    keys={(a,b):hashlib.sha256(bytes([a,b])+b'test-only').digest() for a in range(4) for b in range(a+1,4)}
    nodes=[]
    for i in range(4):
        channel=Channel(i,100+i,{j:keys[min(i,j),max(i,j)] for j in range(4) if j!=i},{j:100+j for j in range(4) if j!=i})
        nodes.append(Node(i,(i*30.,0),3,(90.,0),channel,secret.public_key(),secret if i==3 else None,capacity))
    return nodes

def exchange_beacons(nodes):
    for a,b in [(0,1),(1,0),(1,2),(2,1),(2,3),(3,2)]:
        peer,wire=nodes[a].beacon(b,1.,0,0.);nodes[b].receive(wire,a,.01)

def deliver(nodes,pid=1):
    queue=[(0,*x) for x in nodes[0].originate(pid,0,b'0123456789abcdef',.02)];now=.02
    while queue:
        sender,peer,wire=queue.pop(0);now+=.001;assert len(wire)<=114
        nodes[sender].ack(peer,wire,True,now)
        queue.extend((peer,*x) for x in nodes[peer].receive(wire,sender,now))
    return now

def test_serialized_chain_and_transit_service():
    nodes=setup_nodes();exchange_beacons(nodes);deliver(nodes)
    assert len(nodes[3].delivered)==1
    assert all(n.settlements==1 for n in nodes[:3])
    assert all(n.success_counts=={n.id+1:1} for n in nodes[:3])
    assert nodes[0].cache[1][:4]==(30.,0.,1.,0)

def test_tag_forgery_does_not_consume_replay_window():
    a,b=setup_nodes()[:2];_,wire=a.beacon(1,1.,0,0.)
    corrupt=wire[:-1]+bytes([wire[-1]^1]);assert b.receive(corrupt,0,.01)==[];assert not b.cache
    b.receive(wire,0,.02);assert 0 in b.cache

def test_duplicate_stale_and_wrong_peer_rejected():
    a,b=setup_nodes()[:2];_,wire=a.beacon(1,1.,0,0.)
    assert b.receive(wire,2,.01)==[];assert not b.cache
    b.receive(wire,0,.02);b.receive(wire,0,.03);assert b.rejects['replay']==1
    a.channel.session=99;_,old=a.beacon(1,1.,0,0.);b.receive(old,0,.04);assert b.rejects['unprovisioned session']==1

def test_replay_window_reordering_and_old_bound():
    w=ReplayWindow();assert w.accept(100);assert w.accept(99);assert not w.accept(99);assert not w.accept(36);assert w.accept(37)

def test_signed_receipt_rewrapped_cannot_duplicate_credit():
    nodes=setup_nodes();exchange_beacons(nodes);sent=nodes[0].originate(1,0,b'abc',.02)[0][1];nodes[0].ack(1,sent,True,.021)
    msg=RECEIPT.pack(0,1,100);body=msg+nodes[3].private.sign(SINK+msg)
    for _ in range(2):nodes[0].receive(nodes[1].channel.seal(3,0,body),1,.03)
    assert nodes[0].success_counts=={1:1};assert nodes[0].rejects['duplicate receipt']==1

def test_neighbor_cannot_forge_sink_receipt():
    nodes=setup_nodes();exchange_beacons(nodes);nodes[0].originate(1,0,b'abc',.02)
    msg=RECEIPT.pack(0,1,100)+bytes(64);wire=nodes[1].channel.seal(3,0,msg);nodes[0].receive(wire,1,.03)
    assert nodes[0].rejects['sink signature']==1 and not nodes[0].success_counts

def test_failed_mac_ack_never_credits_valid_receipt():
    nodes=setup_nodes();exchange_beacons(nodes);_,wire=nodes[0].originate(1,0,b'abc',.02)[0];nodes[0].ack(1,wire,False,.021)
    msg=RECEIPT.pack(0,1,100);nodes[0].receive(nodes[1].channel.seal(3,0,msg+nodes[3].private.sign(SINK+msg)),1,.03)
    assert not nodes[0].success_counts and nodes[0].settlements==1

def test_memory_bound_and_expiry_allows_continuation():
    nodes=setup_nodes(capacity=2);exchange_beacons(nodes)
    for i in range(3):nodes[0].originate(i,0,b'a',.02)
    assert len(nodes[0].pending)==2 and nodes[0].evictions==1
    nodes[0].expire(2.1);assert not nodes[0].pending;assert nodes[0].settlements==2

def test_frame_budget_and_loop_history():
    nodes=setup_nodes();exchange_beacons(nodes)
    with pytest.raises(Rejected):nodes[0].originate(1,0,b'x'*25,.02)
    p=Datagram(0,2,100,0,20000,1,1<<1,b'a',bytes(16));wire=nodes[0].channel.seal(2,1,p.encode());nodes[1].receive(wire,0,.03);assert nodes[1].rejects['stale/loop data']==1


def test_large_valid_sequence_jump_has_constant_memory():
    w=ReplayWindow();assert w.accept(0);assert w.accept(2**32-1);assert w.bits==1

def test_source_authentication_survives_forged_hop_wrapper():
    nodes=setup_nodes();p=Datagram(0,1,100,0,20000,3,7,b'fake',bytes(16))
    wire=nodes[2].channel.seal(2,3,p.encode());nodes[3].receive(wire,2,.03)
    assert nodes[3].rejects['source tag']==1 and not nodes[3].delivered

def test_old_source_session_rewrapped_by_neighbor_is_rejected():
    nodes=setup_nodes();p=Datagram(0,1,99,0,20000,3,7,b'old',bytes(16))
    wire=nodes[2].channel.seal(2,3,p.encode());nodes[3].receive(wire,2,.03)
    assert nodes[3].rejects['source session']==1


def test_source_counter_cannot_be_reused_after_expiry():
    nodes=setup_nodes();exchange_beacons(nodes);nodes[0].originate(1,0,b'x',.02);nodes[0].expire(3.)
    with pytest.raises(Rejected,match='source packet counter'):nodes[0].originate(1,0,b'x',3.)

def test_physical_current_integration_and_provenance_guard():
    import importlib.util
    spec=importlib.util.spec_from_file_location('measurements',Path(__file__).resolve().parents[1]/'hardware/validate_measurements.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    samples=[dict(time_s=str(t),voltage_v='3',current_a='.01',provenance='physical') for t in [0,1,2]]
    assert m.validate(samples)==pytest.approx(.06)
    samples[0]['provenance']='synthetic'
    with pytest.raises(ValueError,match='physical provenance'):m.validate(samples)

def test_invalid_measurement_clock_rejected():
    import importlib.util
    spec=importlib.util.spec_from_file_location('measurements',Path(__file__).resolve().parents[1]/'hardware/validate_measurements.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    samples=[dict(time_s='0',voltage_v='3',current_a='.01',provenance='physical')]*2
    with pytest.raises(ValueError,match='strictly increase'):m.validate(samples)

def test_private_provisioning_is_per_node_and_sink_only(tmp_path):
    import subprocess,json,os
    out=tmp_path/'private';script=Path(__file__).resolve().parents[1]/'hardware/provision.py'
    subprocess.run([sys.executable,str(script),'--output',str(out)],check=True,capture_output=True)
    configs=[json.loads((out/f'node_{i}.private.json').read_text()) for i in range(4)]
    assert all('sink_private' not in c for c in configs[:3]);assert 'sink_private' in configs[3]
    assert configs[0]['keys']['1']==configs[1]['keys']['0']
    assert all((out/f'node_{i}.private.json').stat().st_mode&0o777==0o600 for i in range(4))


def test_delayed_first_beacon_and_out_of_order_cache_rejected():
    a,b=setup_nodes()[:2];_,old=a.beacon(1,1.,0,0.)
    b.receive(old,0,1.);assert b.rejects['stale beacon']==1 and not b.cache
    a,b=setup_nodes()[:2];_,old=a.beacon(1,.8,0,0.);_,new=a.beacon(1,.7,0,.1)
    b.receive(new,0,.11);b.receive(old,0,.12)
    assert b.rejects['older beacon']==1 and b.cache[0][2]==pytest.approx(.7)

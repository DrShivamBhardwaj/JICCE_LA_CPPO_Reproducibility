from pathlib import Path
import sys
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wsn_sim.auth_policy import observation,PolicyNode,load_policy
from test_distributed_auth import setup_nodes,exchange_beacons

def state():
    return dict(node=0,xy=[0,0],sink=3,sink_xy=[90,0],own=[1,0],now=.1,
        cache={'1':[30,0,1,0,.01],'2':[45,0,.8,0,.01]},
        links={},lqi={'1':.9,'2':.8},successes={},qos_debts=[0]*6,
        packet=dict(traffic=0,created_us=20000,visited=1,key=[0,1,100]))

def test_stale_visited_and_nonprogress_candidates_excluded():
    s=state();s['cache']['4']=[-10,0,1,0,.01];s['cache']['5']=[50,0,1,0,-1]
    s['packet']['visited']|=1<<2
    obs,mask,ids=observation(s)
    assert obs.shape==(93,) and mask.sum()==1 and ids[0]==1

def test_authenticated_state_and_local_ack_change_features():
    s=state();before,_,_=observation(s)
    s['links']['1']=[9,6,.02];s['qos_debts'][0]=4;s['successes']['2']=3
    after,_,_=observation(s)
    assert not np.array_equal(before,after)
    assert after[7]>.0  # First local delay-debt coordinate.

def test_no_candidates_does_not_create_phantom_sink():
    s=state();s['cache']={};_,mask,ids=observation(s)
    assert not mask.any() and set(ids)=={-2}

def test_checkpoint_replay_and_candidate_permutation():
    root=Path(__file__).resolve().parents[1]
    model=load_policy(root/'outputs/jicce_validation/checkpoints/attention_41001.pt','attention')
    obs,mask,_=observation(state())
    with torch.no_grad():a=model(torch.tensor(obs)[None],torch.tensor(mask)[None])[0]
    swapped=np.r_[obs[:13],obs[13:].reshape(8,10)[[1,0,2,3,4,5,6,7]].ravel()]
    mm=mask[[1,0,2,3,4,5,6,7]]
    with torch.no_grad():b=model(torch.tensor(swapped)[None],torch.tensor(mm)[None])[0]
    np.testing.assert_allclose(a.numpy()[:,[1,0,2,3,4,5,6,7]],b.numpy(),atol=1e-6)

def test_policy_runs_inside_authenticated_chain_and_settles_transit():
    old=setup_nodes();root=Path(__file__).resolve().parents[1]
    model=load_policy(root/'outputs/jicce_validation/checkpoints/attention_41001.pt','attention')
    audit=[]
    nodes=[PolicyNode(n.id,n.xy,n.sink,n.sink_xy,n.channel,n.public,n.private,
        model=model,arm='attention',audit=audit.append) for n in old]
    exchange_beacons(nodes)
    queue=[(0,*a) for a in nodes[0].originate(0,0,b'fixture',.02)];now=.02
    while queue:
        sender,peer,wire=queue.pop(0);now+=.001
        nodes[sender].ack(peer,wire,True,now)
        queue.extend((peer,*a) for a in nodes[peer].receive_with_lqi(wire,sender,now,200))
    assert nodes[-1].delivered_total==1 and len(audit)==3
    assert all(n.settlements==1 for n in nodes[:-1])
    assert nodes[0].source_deliveries[0]['pid']==0

"""Offline reconstruction of actions, frame reception and forwarding proofs."""
import gzip,json,hashlib,sys
from pathlib import Path
import numpy as np
import torch,yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic,MaskedActorCritic
torch.set_num_threads(1)
counts=dict(runs=0,decisions=0,received_data=0,received_proofs=0,timeouts=0,multihop_deliveries=0)
for line in gzip.open(ROOT/'outputs/ns3_multihop/trace.jsonl.gz','rt'):
 r=json.loads(line)
 if r['type']=='run':
  counts['runs']+=1;xy=np.array(r['positions']).reshape(-1,2);faults=set(r['fault_nodes']);decisions={};rx=set();proofs=set();delivered=set()
  cfg=yaml.safe_load((ROOT/'configs/af_v3_final.yaml').read_text());env=PacketRoutingEnv(cfg);b=env.builder
  cp=ROOT/f"outputs/jicce_validation/checkpoints/{r['arm']}_{41001+r['seed']-75001}.pt";assert hashlib.sha256(cp.read_bytes()).hexdigest()==r['checkpoint_sha256'];w=torch.load(cp,weights_only=True,map_location='cpu')
  m=LocalAttentionActorCritic(b.context_dim,b.CANDIDATE_DIM,b.k,hidden=cfg['rl']['hidden'],n_costs=env.n_costs) if r['arm']=='attention' else MaskedActorCritic(b.obs_dim,b.k,hidden=w['encoder.0.weight'].shape[0],n_costs=env.n_costs)
  m.load_state_dict(w);m.eval()
 elif r['type']=='decision':
  counts['decisions']+=1;assert np.linalg.norm(xy[r['node']]-xy[r['peer']])<=50+1e-8
  if r['previous']>=0:assert (r['pid'],r['node'],r['previous']) in rx and r['node'] not in faults
  with torch.no_grad():logits,_,_=m(torch.tensor(r['obs']).unsqueeze(0),torch.tensor(r['mask']).unsqueeze(0))
  assert int(logits.argmax())==r['action'];target=r['candidates'][r['action']];assert (len(xy)-1 if target<0 else target)==r['peer'];decisions[(r['pid'],r['node'])]=r
 elif r['type']=='mac':
  if r['kind']==1:
   counts['received_data']+=1;assert (r['pid'],r['peer']) in decisions;assert decisions[(r['pid'],r['peer'])]['peer']==r['node'];rx.add((r['pid'],r['node'],r['peer']))
   if r['node']==len(xy)-1 and decisions[(r['pid'],r['peer'])]['previous']>=0:counts['multihop_deliveries']+=1
  elif r['kind']==2:
   counts['received_proofs']+=1;d=decisions[(r['pid'],r['peer'])];assert d['previous']==r['node'];assert (r['pid'],d['peer'],r['peer']) in rx;assert np.linalg.norm(xy[r['node']]-xy[r['peer']])<=50+1e-8
 elif r['type']=='timeout':counts['timeouts']+=1
assert counts['runs']==120 and counts['multihop_deliveries']>0 and counts['received_proofs']>0
(ROOT/'outputs/ns3_multihop/verification.json').write_text(json.dumps(dict(status='passed',**counts,scope='trace consistency and frozen-action reconstruction; no external packet capture or full observation reconstruction'),indent=2))
print(counts)

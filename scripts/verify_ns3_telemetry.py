"""Rebuild every observation/action and check local risk and energy identities."""
import gzip,json,hashlib,sys
from pathlib import Path
import numpy as np
import torch,yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.ns3_telemetry import TelemetryBuilder
from wsn_sim.security import SecurityRiskEstimator
from wsn_sim.qos import QoSDebtTracker
from wsn_sim.rl import LocalAttentionActorCritic,MaskedActorCritic
from wsn_sim.env import PacketRoutingEnv
torch.set_num_threads(1);out=ROOT/'outputs/ns3_telemetry';counts=dict(runs=0,decisions=0,energy_identities=0,proofs=0,timeouts=0)
for path in sorted(out.glob('trace_*.jsonl.gz')):
 for line in gzip.open(path,'rt'):
  r=json.loads(line)
  if r['type']=='run':
   counts['runs']+=1;xy=np.array(r['positions']);n=len(xy)-1;builder=TelemetryBuilder(xy,[.09,.35,1.5]);arm=r['arm'];seed=r['seed'];sources=r['sources'];classes=r['classes'];faults=set(r['faults']);risk=[SecurityRiskEstimator(n,enabled=arm not in ['attention_no_risk','attention_no_proof']) for _ in range(n)];watches={};decisions={};rx=set();beacons={};generated={};cfg=yaml.safe_load((ROOT/'configs/af_v3_final.yaml').read_text());env=PacketRoutingEnv(cfg);policy='capacity_mlp' if arm=='capacity_mlp' else 'attention';cp=ROOT/f'outputs/jicce_validation/checkpoints/{policy}_{41001+seed-76001}.pt';assert hashlib.sha256(cp.read_bytes()).hexdigest()==r['checkpoint_sha256'];w=torch.load(cp,map_location='cpu',weights_only=True);model=LocalAttentionActorCritic(13,10,8,hidden=cfg['rl']['hidden'],n_costs=env.n_costs) if policy=='attention' else MaskedActorCritic(93,8,hidden=w['encoder.0.weight'].shape[0],n_costs=env.n_costs);model.load_state_dict(w);model.eval()
  elif r['type']=='beacon_sent':beacons[(r['node'],r['time'])]=(r['energy'],r['queue'])
  elif r['type']=='decision':
   counts['decisions']+=1;raw=r['raw'];node=r['node'];pid=r['pid'];prev=r['previous']
   if prev<0:generated[pid]=r['time'];assert node==sources[pid]
   else:assert (pid,node,prev) in rx and node not in faults
   assert np.allclose(raw['a'],risk[node].a) and np.allclose(raw['b'],risk[node].b)
   cache={int(k):tuple(v) for k,v in raw['cache'].items()};links={int(k):tuple(v) for k,v in raw['links'].items()}
   for peer,(energy,queue,stamp,lqi) in cache.items():assert np.allclose([energy,queue],beacons[(peer,stamp)]) and 0<=lqi<=1
   q=QoSDebtTracker([90,350,1500],[.985,.96,.90],[.015,.04,.10]);q.delay_debt=np.array(raw['delay_debt']);q.loss_debt=np.array(raw['loss_debt'])
   obs=builder.build(node,classes[pid],r['time']-generated.get(pid,.4+pid*(.002 if 'congested' in r['setting'] else .02)),set(raw['visited']),r['time'],raw['own'],cache,links,risk[node],q)
   # Sources without candidates can still generate a packet later seen nowhere;
   # every forwarded packet has an earlier successful source decision in this trace.
   assert np.allclose(obs.flat_obs,r['obs'],atol=1e-7) and np.array_equal(obs.mask,r['mask']) and np.array_equal(obs.node_ids,r['candidates'])
   with torch.no_grad():logits,_,_=model(torch.tensor(obs.flat_obs).unsqueeze(0),torch.tensor(obs.mask).unsqueeze(0))
   assert int(logits.argmax())==r['action'];peer=r['peer'];assert np.linalg.norm(xy[node]-xy[peer])<=50+1e-8;decisions[(node,pid)]=r
   if peer<n and arm!='attention_no_proof':
    a,b,_=links.get(peer,(9.,1.,.005));watches[(node,peer,pid)]=a/(a+b)
  elif r['type']=='mac':
   pid=r['pid'];node=r['node'];peer=r['peer']
   if r['kind']==1:
    assert decisions[(peer,pid)]['peer']==node;rx.add((pid,node,peer))
   elif r['kind']==2:
    assert decisions[(peer,pid)]['previous']==node;d=decisions[(peer,pid)];assert (pid,d['peer'],peer) in rx
    key=(node,peer,pid)
    if key in watches:risk[node].observe_forward(peer,True,watches.pop(key));counts['proofs']+=1
   elif r['kind']==6:assert np.linalg.norm(xy[node]-xy[peer])<=50+1e-8
  elif r['type']=='timeout':
   key=(r['node'],r['peer'],r['pid']);assert np.isclose(watches.pop(key),r['expected']);risk[key[0]].observe_forward(key[1],False,r['expected']);counts['timeouts']+=1
  elif r['type']=='final':
   tele=np.array(r['telemetry']);expected=3*(tele[:,6]*.0174+tele[:,7]*.0188+tele[:,8]*.000020);assert np.allclose(expected,tele[:,0],atol=1e-10);assert np.allclose(tele[:,6:].sum(1),4.,atol=1e-8);assert np.isclose(tele[:n,0].sum(),r['radio_energy_j']);counts['energy_identities']+=len(tele)
assert counts['runs']==600
(out/'verification.json').write_text(json.dumps(dict(status='passed',**counts,limits='Internal trace reconstruction, not independent capture; QoS debt snapshots and link telemetry not independently replayed'),indent=2));print(counts)

"""Replay the frozen feedback ledger, complete observations and model actions."""
import gzip,json,hashlib,sys
from pathlib import Path
import numpy as np
import torch,yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.ns3_telemetry import TelemetryBuilder
from wsn_sim.censored_feedback import FeedbackLedger
from wsn_sim.qos import QoSDebtTracker
from wsn_sim.rl import LocalAttentionActorCritic,MaskedActorCritic
from wsn_sim.env import PacketRoutingEnv
torch.set_num_threads(1);out=ROOT/'outputs/ns3_censored';counts=dict(runs=0,decisions=0,energy_identities=0,passive_observations=0,evidence_updates=0,censored_expirations=0)
mode_by_arm={'censored_passive':'censored','naive_passive':'naive','active_proof':'active','frozen_prior':'frozen','capacity_mlp_censored':'censored'}
for path in sorted(out.glob('trace_*.jsonl.gz')):
 for line in gzip.open(path,'rt'):
  r=json.loads(line)
  if r['type']=='run':
   counts['runs']+=1;xy=np.array(r['positions']);n=len(xy)-1;builder=TelemetryBuilder(xy,[.09,.35,1.5]);arm=r['arm'];seed=r['seed'];sources=r['sources'];classes=r['classes'];faults=set(r['faults']);ledger=FeedbackLedger(n,mode_by_arm[arm]);decisions={};rx=set();beacons={};generated={};requests={};tick=-1;expire_queue=[];cfg=yaml.safe_load((ROOT/'configs/af_v3_final.yaml').read_text());env=PacketRoutingEnv(cfg);policy='capacity_mlp' if arm=='capacity_mlp_censored' else 'attention';cp=ROOT/f'outputs/jicce_validation/checkpoints/{policy}_{41001+seed-77001}.pt';assert hashlib.sha256(cp.read_bytes()).hexdigest()==r['checkpoint_sha256'];w=torch.load(cp,map_location='cpu',weights_only=True);model=LocalAttentionActorCritic(13,10,8,hidden=cfg['rl']['hidden'],n_costs=env.n_costs) if policy=='attention' else MaskedActorCritic(93,8,hidden=w['encoder.0.weight'].shape[0],n_costs=env.n_costs);model.load_state_dict(w);model.eval()
  elif r['type']=='beacon_sent':beacons[(r['node'],r['time'])]=(r['energy'],r['queue'])
  elif r['type']=='decision':
   counts['decisions']+=1;raw=r['raw'];node=r['node'];pid=r['pid'];prev=r['previous']
   if prev<0:generated[pid]=r['time'];assert node==sources[pid]
   else:assert (pid,node,prev) in rx and node not in faults
   assert np.allclose(raw['a'],ledger.risk[node].a) and np.allclose(raw['b'],ledger.risk[node].b)
   cache={int(k):tuple(v) for k,v in raw['cache'].items()};links={int(k):tuple(v) for k,v in raw['links'].items()}
   for peer,(energy,queue,stamp,lqi) in cache.items():assert np.allclose([energy,queue],beacons[(peer,stamp)]) and 0<=lqi<=1
   q=QoSDebtTracker([90,350,1500],[.985,.96,.90],[.015,.04,.10]);q.delay_debt=np.array(raw['delay_debt']);q.loss_debt=np.array(raw['loss_debt'])
   obs=builder.build(node,classes[pid],r['time']-generated[pid],set(raw['visited']),r['time'],raw['own'],cache,links,ledger.risk[node],q)
   assert np.allclose(obs.flat_obs,r['obs'],atol=1e-7) and np.array_equal(obs.mask,r['mask']) and np.array_equal(obs.node_ids,r['candidates'])
   with torch.no_grad():logits,_,_=model(torch.tensor(obs.flat_obs).unsqueeze(0),torch.tensor(obs.mask).unsqueeze(0))
   assert int(logits.argmax())==r['action'];peer=r['peer'];assert np.linalg.norm(xy[node]-xy[peer])<=50+1e-8;decisions[(node,pid)]=r;requests[(node,peer,pid)]=True
   if peer<n:
    a,b,_=links.get(peer,(9.,1.,.005));ledger.register(node,peer,pid,r['time'],a/(a+b))
  elif r['type']=='mac':
   pid=r['pid'];node=r['node'];peer=r['peer']
   # Positive records close silently at poll boundaries. Close only those
   # whose expiry preceded the current callback's poll, preserving callbacks
   # arriving within the same poll as their nominal expiry.
   boundary=(np.ceil(r['time']*1000-1e-8)-1)/1000
   for watch in ledger.watches.values():
    if not watch.closed and watch.seen>0 and watch.expiry is not None and watch.expiry<=boundary:watch.closed=True
   if r['kind']==1:
    assert decisions[(peer,pid)]['peer']==node;rx.add((pid,node,peer))
   elif r['kind']==2:
    assert arm=='active_proof';d=decisions[(peer,pid)];assert d['previous']==node and (pid,d['peer'],peer) in rx;ledger.evidence(node,peer,pid,'proof',r['time'])
   elif r['kind']==7:
    counts['passive_observations']+=1;d=decisions[(peer,pid)];assert (node,peer,pid) in ledger.watches and d['previous']==node and d['peer']!=node;assert np.linalg.norm(xy[node]-xy[peer])<=50+1e-8;ledger.evidence(node,peer,pid,'passive',r['time'])
   elif r['kind']==6:
    assert any(x[0]==pid and x[1]==n for x in rx)
    assert np.linalg.norm(xy[node]-xy[peer])<=50+1e-8;ledger.evidence(node,peer,pid,'receipt',r['time'])
   elif r['kind']==3 and (node,peer,pid) in requests:
    requests.pop((node,peer,pid));ledger.acknowledge(node,peer,pid,bool(r['ok']),r['time'])
  elif r['type']=='observation_expired':
   # Expiration is evaluated once at the poll boundary, after that tick's MAC
   # callbacks. Replaying on the first record enqueues all simultaneous updates.
   if not expire_queue:expire_queue=ledger.expire(r['time'])
   assert expire_queue.pop(0)==(r['node'],r['peer'],r['pid']);counts['censored_expirations']+=1
  elif r['type']=='evidence_update':
   expected=ledger.updates.pop(0);assert expected['key']==r['key'] and expected['success']==r['success'] and np.isclose(expected['weight'],r['weight']) and np.isclose(expected['time'],r['time']);counts['evidence_updates']+=1
  elif r['type']=='final':
   # Watches with existing positive evidence expire without a log or update.
   ledger.expire(4.);assert not ledger.updates
   tele=np.array(r['telemetry']);assert np.allclose(3*(tele[:,6]*.0174+tele[:,7]*.0188+tele[:,8]*.000020),tele[:,0],atol=1e-10);assert np.allclose(tele[:,6:].sum(1),4.,atol=1e-8);assert np.isclose(tele[:n,0].sum(),r['radio_energy_j']);counts['energy_identities']+=len(tele)
   if arm!='active_proof':assert r['proof_requests']==0
   if mode_by_arm[arm] in ['censored','frozen']:assert r['negative_updates']==0 and all(np.allclose(x.b,1) for x in ledger.risk)
assert counts['runs']==750
(out/'verification.json').write_text(json.dumps(dict(status='passed',**counts,limits='Internal trace reconstruction; beacon receive callbacks and QoS/link histories not independently replayed; no external capture or authentication'),indent=2));print(counts)

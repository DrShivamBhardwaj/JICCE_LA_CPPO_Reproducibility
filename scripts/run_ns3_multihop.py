"""Exploratory frozen-policy transfer to ns-3 MAC; synthetic features retained.
No training, simulator outcome selection, hardware or live IDS claim.
"""
import ctypes as C
import gzip,hashlib,json,sys,argparse
from pathlib import Path
import numpy as np
import torch,yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic,MaskedActorCritic
class Event(C.Structure):
    _fields_=[('time',C.c_double)]+[(x,C.c_int) for x in ['kind','node','peer','pid','ok']]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fixtures',type=int,default=30);parser.add_argument('--start',type=int,default=75001);parser.add_argument('--packets',type=int,default=30);parser.add_argument('--output',default='ns3_multihop');args=parser.parse_args()
    torch.set_num_threads(1)
    lib=C.CDLL(str(ROOT/'build/libwsn_ns3.so'));lib.bridge_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double];lib.bridge_step.argtypes=[C.c_double];lib.bridge_poll.argtypes=[C.POINTER(Event)]
    out=ROOT/'outputs'/args.output;out.mkdir(parents=True,exist_ok=True);summaries=[]
    with gzip.open(out/'trace.jsonl.gz','wt') as trace:
      def log(**kw):trace.write(json.dumps(kw)+'\n')
      for seed in range(args.start,args.start+args.fixtures):
       for attack in [False,True]:
        for arm in ['attention','capacity_mlp']:
         cfg=yaml.safe_load((ROOT/'configs/af_v3_final.yaml').read_text());cfg['seed']=seed;cfg['attack']['malicious_ratio']=0
         env=PacketRoutingEnv(cfg);b=env.builder;n=env.net.n
         cp=ROOT/f'outputs/jicce_validation/checkpoints/{arm}_{41001+seed-args.start}.pt';weights=torch.load(cp,weights_only=True,map_location='cpu')
         model=LocalAttentionActorCritic(b.context_dim,b.CANDIDATE_DIM,b.k,hidden=cfg['rl']['hidden'],n_costs=env.n_costs) if arm=='attention' else MaskedActorCritic(b.obs_dim,b.k,hidden=weights['encoder.0.weight'].shape[0],n_costs=env.n_costs)
         model.load_state_dict(weights);model.eval()
         xy=np.vstack([env.net.positions,env.net.sink]).astype(np.float64).ravel();lib.bridge_init(n+1,xy.ctypes.data_as(C.POINTER(C.c_double)),seed,env.net.radio_range)
         rng=np.random.default_rng(seed+100000);faults=set(map(int,rng.choice(n,n//4,replace=False))) if attack else set()
         sources=np.random.default_rng(seed+200000).integers(0,n,args.packets);classes=np.random.default_rng(seed+300000).choice(3,args.packets,p=[.35,.45,.2])
         run=dict(seed=seed,attack=attack,arm=arm);log(type='run',**run,checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),positions=xy.tolist(),fault_nodes=sorted(faults),sources=sources.tolist(),classes=classes.tolist())
         now=0.;delivered={};watches={};visited={};created={};decisions=0;acks=0;proofs=0;timeouts=0;critical_violations=0
         def route(node,pid,previous):
          nonlocal decisions
          if node in visited[pid] or len(visited[pid])>=22:return
          visited[pid].add(node)
          obs=b.build(env.net,env.sec,env.qos,node,int(classes[pid]),now-created[pid],visited[pid])
          if not obs.mask.any():return
          with torch.no_grad(): logits,_,_=model(torch.tensor(obs.flat_obs).unsqueeze(0),torch.tensor(obs.mask).unsqueeze(0))
          action=int(logits.argmax());target=int(obs.node_ids[action]);peer=n if target<0 else target
          assert env.net.distance(node,None if target<0 else target)<=env.net.radio_range+1e-9
          log(type='decision',**run,time=now,pid=pid,node=node,peer=peer,previous=previous,obs=obs.flat_obs.tolist(),mask=obs.mask.tolist(),candidates=obs.node_ids.tolist(),action=action)
          if target>=0:watches[(node,target,pid)]=now+.15
          lib.bridge_send(node,peer,pid,previous);decisions+=1
         for pid,source in enumerate(sources):
          created[pid]=now;visited[pid]=set();route(int(source),pid,-1)
          for _ in range(300):
           lib.bridge_step(.001);now+=.001
           event=Event()
           while lib.bridge_poll(C.byref(event)):
            e={x:getattr(event,x) for x in ['time','kind','node','peer','pid','ok']};log(type='mac',**run,**e)
            p=event.pid
            if event.kind==1:
             if event.node==n:delivered[p]=event.time-created[p]
             elif event.node not in faults:route(event.node,p,event.peer)
            elif event.kind==2:
             key=(event.node,event.peer,p)
             if key in watches:
              del watches[key];env.sec.observe_forward(event.peer,True,1.);proofs+=1
            elif event.kind==3:acks+=event.ok
           for key,expiry in list(watches.items()):
            if now>=expiry:
             del watches[key];env.sec.observe_forward(key[1],False,1.);timeouts+=1;log(type='timeout',**run,time=now,node=key[0],peer=key[1],pid=key[2])
          if classes[pid]==0 and (pid not in delivered or delivered[pid]>.09):critical_violations+=1
         lib.bridge_destroy()
         row=dict(**run,packets=args.packets,delivered=len(delivered),delivery=len(delivered)/args.packets,critical_packets=int(sum(classes==0)),critical_violations=critical_violations,decisions=decisions,mac_success_confirms=acks,forwarding_proofs=proofs,forwarding_timeouts=timeouts,mean_delivered_delay_s=float(np.mean(list(delivered.values()))) if delivered else None)
         summaries.append(row);print(row,flush=True)
    (out/'summary.json').write_text(json.dumps(summaries,indent=2))
if __name__=='__main__':main()

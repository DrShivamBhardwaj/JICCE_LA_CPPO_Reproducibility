"""Frozen receipt-assisted censored passive feedback evaluation."""
import ctypes as C
import gzip,hashlib,json,sys,argparse,io
from pathlib import Path
import numpy as np
import torch,yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic,MaskedActorCritic
from wsn_sim.ns3_telemetry import TelemetryBuilder
from wsn_sim.censored_feedback import FeedbackLedger
from wsn_sim.qos import QoSDebtTracker
class Event(C.Structure):
 _fields_=[('time',C.c_double)]+[(x,C.c_int) for x in ['kind','node','peer','pid','ok']]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--duration',type=float,required=True);ap.add_argument('--interval',type=float,default=.2);ap.add_argument('--pilot',action='store_true');ap.add_argument('--seed-list');ap.add_argument('--start',type=int,default=77001);ap.add_argument('--end',type=int,default=77030);args=ap.parse_args();torch.set_num_threads(1)
 protocol=json.loads((ROOT/'configs/ns3_censored_protocol.json').read_text());out=ROOT/'outputs'/'review_long_horizon'/f'{int(args.duration)}s_{args.start}';protocol.update(horizon_s=args.duration,packets=int((args.duration-2)/args.interval),arms=['active_proof','censored_passive','frozen_prior'],settings=[dict(name='blackhole',attack=.25,interval_s=args.interval,reference_loss_db=40.)],status='post-review exploratory stress test; not confirmatory',parent_source='ea747d8a86aa8f848002d3101adf58e30270f0b2');out.mkdir(parents=True,exist_ok=True)
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2));lib=C.CDLL(str(ROOT/'build/libwsn_ns3_passive.so'))
 lib.bridge_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double];lib.bridge_step.argtypes=[C.c_double];lib.bridge_poll.argtypes=[C.POINTER(Event)];lib.bridge_options.argtypes=[C.c_int,C.c_double];lib.bridge_telemetry.argtypes=[C.c_int,C.POINTER(C.c_double)]
 seeds=[76901] if args.pilot else ([int(s) for s in args.seed_list.split(',')] if args.seed_list else range(args.start,args.end+1));summaries=[]
 for index,seed in enumerate(seeds):
  with io.StringIO() as trace:
   def log(**kw):
    if kw.get('type') in ('run','final','evidence_update','observation_expired'):trace.write(json.dumps(kw,separators=(',',':'))+'\n')
   for setting in protocol['settings']:
    for arm in protocol['arms']:
     cfg=yaml.safe_load((ROOT/'configs/af_v3_final.yaml').read_text());cfg['seed']=seed;cfg['attack']['malicious_ratio']=0;env=PacketRoutingEnv(cfg);n=env.net.n
     xy=np.vstack([env.net.positions,env.net.sink]).astype(np.float64);builder=TelemetryBuilder(xy,[.09,.35,1.5]);policy='capacity_mlp' if arm=='capacity_mlp_censored' else 'attention';cp=ROOT/f'outputs/jicce_validation/checkpoints/{policy}_{41001+(0 if args.pilot else seed-84001)}.pt';weights=torch.load(cp,weights_only=True,map_location='cpu')
     model=LocalAttentionActorCritic(13,10,8,hidden=cfg['rl']['hidden'],n_costs=env.n_costs) if policy=='attention' else MaskedActorCritic(93,8,hidden=weights['encoder.0.weight'].shape[0],n_costs=env.n_costs);model.load_state_dict(weights);model.eval()
     proof_on=arm=='active_proof';lib.bridge_options(proof_on,setting['reference_loss_db']);flat=xy.ravel();lib.bridge_init(n+1,flat.ctypes.data_as(C.POINTER(C.c_double)),seed,50.)
     mode={'censored_passive':'censored','capacity_mlp_censored':'censored','naive_passive':'naive','active_proof':'active','frozen_prior':'frozen'}[arm];ledger=FeedbackLedger(n,mode);risks=ledger.risk;qos=[QoSDebtTracker([90,350,1500],[.985,.96,.90],[.015,.04,.10]) for _ in range(n)]
     cache=[{} for _ in range(n+1)];links=[{} for _ in range(n+1)];tele=np.zeros((n+1,9));beacons={};nextbeacon=np.arange(n+1)*.003;beaconserial=0
     faults=set(map(int,np.random.default_rng(seed+100000).choice(n,round(n*setting['attack']),replace=False)))
     sources=np.random.default_rng(seed+200000).integers(0,n,protocol['packets']);classes=np.random.default_rng(seed+300000).choice(3,len(sources),p=[.35,.45,.2]);generated={};visited={};previous={};delivered={};receipted=set();settled=set();watches={};requests={};now=0.;nextpid=0;peak_pending=0;peak_watches=0;handle_exhaustions=0;samples=[];false_timeouts=0;timeouts=0;successproofs=0;data_failures=0;decisioncount=0;beaconrx=0
     run=dict(seed=seed,setting=setting['name'],arm=arm);log(type='run',**run,positions=xy.tolist(),faults=sorted(faults),sources=sources.tolist(),classes=classes.tolist(),checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest())
     def telemetry(node):
      a=(C.c_double*9)();lib.bridge_telemetry(node,a);tele[node]=list(a);return (max(0.,1-tele[node,0]/.5),min(1.,tele[node,1]/32))
     def route(node,pid,prev):
      nonlocal decisioncount
      if node in visited[pid] or len(visited[pid])>=22 or telemetry(node)[0]<=0:return
      visited[pid].add(node);previous[(pid,node)]=prev
      obs=builder.build(node,int(classes[pid]),now-generated[pid],visited[pid],now,telemetry(node),cache[node],links[node],risks[node],qos[node])
      if not obs.mask.any():log(type='no_candidate',**run,time=now,pid=pid,node=node);return
      with torch.no_grad():logits,_,_=model(torch.tensor(obs.flat_obs).unsqueeze(0),torch.tensor(obs.mask).unsqueeze(0))
      action=int(logits.argmax());target=int(obs.node_ids[action]);peer=n if target<0 else target
      raw=dict(own=telemetry(node),cache={str(k):list(v) for k,v in cache[node].items()},links={str(k):list(v) for k,v in links[node].items()},a=risks[node].a.tolist(),b=risks[node].b.tolist(),delay_debt=qos[node].delay_debt.tolist(),loss_debt=qos[node].loss_debt.tolist(),visited=sorted(visited[pid]))
      log(type='decision',**run,time=now,pid=pid,node=node,peer=peer,previous=prev,obs=obs.flat_obs.tolist(),mask=obs.mask.tolist(),candidates=obs.node_ids.tolist(),action=action,raw=raw)
      pdr=links[node].get(peer,(9.,1.,.005));expected=pdr[0]/sum(pdr[:2]);requests[(node,peer,pid)]=now
      if target>=0:ledger.register(node,target,pid,now,expected)
      lib.bridge_send(node,peer,pid,prev);decisioncount+=1
     for tick in range(int(protocol['horizon_s']/.001)):
      now=tick*.001
      if tick%1000==0:
       for node in range(n+1):telemetry(node)
       peak_pending=max(peak_pending,int(tele[:,1].max()));peak_watches=max(peak_watches,len(ledger.watches))
       samples.append(dict(time=now,pending_max=int(tele[:,1].max()),watches=len(ledger.watches),delivered=len(delivered),generated=len(generated),energy_j=float(tele[:n,0].sum()),debt_max=float(max(max(q.delay_debt) for q in qos))))
      for node in np.flatnonzero(nextbeacon<=now):
       own=telemetry(int(node));beaconserial+=1;beacons[beaconserial]=(*own,now);lib.bridge_beacon(int(node),beaconserial);log(type='beacon_sent',**run,time=now,node=int(node),sequence=beaconserial,energy=own[0],queue=own[1]);nextbeacon[node]+=.5
      while nextpid<len(sources) and now>=.4+nextpid*setting['interval_s']-1e-9:
       pid=nextpid;generated[pid]=now;visited[pid]=set();route(int(sources[pid]),pid,-1);nextpid+=1
      lib.bridge_step(.001);now=(tick+1)*.001;e=Event()
      while lib.bridge_poll(C.byref(e)):
       if e.kind==7 and (e.node,e.peer,e.pid) not in ledger.watches:continue
       if e.kind==5:
        energy,queue,stamp=beacons[e.pid];cache[e.node][e.peer]=(energy,queue,stamp,e.ok/255.);beaconrx+=1;continue
       r={k:getattr(e,k) for k in ['time','kind','node','peer','pid','ok']};log(type='mac',**run,**r);pid=e.pid
       if e.kind==4:handle_exhaustions+=1
       if e.kind==1:
        if e.node==n:
         if pid not in delivered:
          delivered[pid]=e.time-generated[pid];lib.bridge_receipt(n,e.peer,pid)
        elif e.node not in faults:route(e.node,pid,e.peer)
       elif e.kind==2:
        ledger.evidence(e.node,e.peer,pid,'proof',e.time)
       elif e.kind==7:
        ledger.evidence(e.node,e.peer,pid,'passive',e.time)
       elif e.kind==3:
        key=(e.node,e.peer,pid)
        if key in requests:
         ledger.acknowledge(e.node,e.peer,pid,bool(e.ok),e.time);start=requests.pop(key);a,b,d=links[e.node].get(e.peer,(9.,1.,.005));links[e.node][e.peer]=(a+bool(e.ok),b+int(not e.ok),.8*d+.2*(e.time-start));data_failures+=int(not e.ok)
       elif e.kind==6:
        ledger.evidence(e.node,e.peer,pid,'receipt',e.time)
        prev=previous.get((pid,e.node),-1)
        if prev>=0:lib.bridge_receipt(e.node,prev,pid)
        elif e.node==sources[pid]:
         receipted.add(pid)
         if pid not in settled:qos[e.node].update(int(classes[pid]),True,now-generated[pid]);settled.add(pid)
      for key in ledger.expire(now):
       timeouts+=1;false_timeouts+=key[1] not in faults;log(type='observation_expired',**run,time=now,node=key[0],peer=key[1],pid=key[2])
      while ledger.updates:
       log(type='evidence_update',**run,**ledger.updates.pop(0))
      for pid in generated.keys()-settled:
       if now-generated[pid]>=1.5:qos[int(sources[pid])].update(int(classes[pid]),False,None);settled.add(pid)
     for node in range(n+1):telemetry(node)
     critical=[p for p,c in enumerate(classes) if c==0];violations=sum(p not in delivered or delivered[p]>.09 for p in critical);energy=float(tele[:n,0].sum());totalbytes=len(delivered)*52
     row=dict(**run,duration_s=args.duration,interval_s=args.interval,peak_pending=peak_pending,peak_watches=peak_watches,handle_exhaustions=handle_exhaustions,terminal_source_debt_max=float(max(max(q.delay_debt) for q in qos)),samples=samples,packets=len(sources),delivered=len(delivered),delivery=len(delivered)/len(sources),critical_packets=len(critical),critical_violation=violations/len(critical),radio_energy_j=energy,energy_per_delivered_byte=energy/totalbytes if totalbytes else None,sink_energy_j=float(tele[n,0]),phy_tx_frames=int(tele[:,2].sum()),phy_tx_bytes=int(tele[:,3].sum()),proof_requests=int(tele[:,4].sum()),data_requests=int(tele[:,5].sum()),beacon_requests=beaconserial,beacon_receptions=beaconrx,positive_updates=ledger.positives,negative_updates=ledger.failures,censored_events=ledger.censored,timeouts=timeouts,benign_relay_timeouts=int(false_timeouts),data_mac_failures=data_failures,decisions=decisioncount,source_receipts=len(receipted),mean_delivered_delay_s=float(np.mean(list(delivered.values()))) if delivered else None)
     log(type='final',**row,telemetry=tele.tolist());summaries.append(row);lib.bridge_destroy();print(json.dumps(row),flush=True)
     (out/f'summary_{args.start}_{args.end}.json').write_text(json.dumps(summaries,indent=2))
   target=out/f'trace_{seed}.jsonl.gz';temporary=target.with_suffix('.tmp');temporary.write_bytes(gzip.compress(trace.getvalue().encode(),compresslevel=6,mtime=0));temporary.replace(target)
 if not args.pilot and not args.seed_list and args.start==77001 and args.end==77030:
  (out/'summary.json').write_text(json.dumps(summaries,indent=2))
if __name__=='__main__':main()

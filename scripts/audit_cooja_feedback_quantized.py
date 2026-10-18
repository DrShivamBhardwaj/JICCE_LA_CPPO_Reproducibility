"""Replay ledger and wires; reproduce the declared float32-to-integer cache-age representation."""
from pathlib import Path
import sys,json,re,struct,hmac,hashlib,math,argparse,collections,gzip
import numpy as np
import torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'src'))
from wsn_sim.censored_feedback import FeedbackLedger
from wsn_sim.auth_policy import load_policy
from wsn_sim.distributed_auth import HEADER,DOMAIN,SOURCE,SINK,Datagram
XY=np.array([[0,0],[45,15],[45,-15],[90,0]],float);MODES=['censored','active','naive','frozen']
_MODEL=None

def features(v,node,ledger):
 c=np.array(struct.unpack('!44f',bytes.fromhex(v['cache_hex']))).reshape(4,11);now=v['now_ms']/1000;traffic=v['traffic'];deadlines=[.09,.35,1.5];current=math.dist(XY[node],XY[3]);scored=[];risk=ledger.risk[node]
 for peer,row in enumerate(c):
  x,y,e,q,stamp,lqi,a,b,delay,success,valid=row
  if not valid or ((v['now_ms']-int(np.float32(np.float32(stamp)*np.float32(1000))))&0xffffffff)>750 or e<=0 or v['visited']&(1<<peer):continue
  progress=current-math.dist([x,y],XY[3]);
  if progress<=0:continue
  pdr=a/(a+b);rr=[float(peer==3),e,pdr,lqi,q,np.clip(progress/38,-1,1),0 if peer==3 else risk.risk[peer],0 if peer==3 else risk.risk_ucb[peer],min(1/pdr-1,4)/4,min(delay/deadlines[traffic],2)/2]
  score=1.25*progress/38+.75*pdr+.25*e-.55*rr[7]-.2*q;scored.append((score,peer,rr))
 scored.sort(key=lambda x:(-x[0],x[1]));ids=[p for _,p,_ in scored[:8]];obs=np.zeros(93,np.float32);obs[0]=1;obs[2]=min(current/math.hypot(150,150),1);obs[3]=np.clip(1-max(0,(v['now_ms']-v['created_ms'])/1000)/deadlines[traffic],0,1);obs[4+traffic]=1;debt=np.array(struct.unpack('!6f',bytes.fromhex(v['qos_hex'])));obs[7:13]=debt/(1+debt)
 for i,(_,_,row) in enumerate(scored[:8]):obs[13+10*i:23+10*i]=row
 return obs,ids

def audit_run(folder):
 global _MODEL
 folder=Path(folder);events=[];logpath=folder/'COOJA.testlog';raw=logpath.read_bytes() if logpath.exists() else gzip.decompress((folder/'COOJA.testlog.gz').read_bytes());text=raw.decode();assert 'TEST OK' in text
 for line in text.splitlines():
  m=re.match(r'^(\d+) node-(\d+) (\{.*\})$',line)
  if m:
   v=json.loads(m[3]);v['_node']=int(m[2])-1;v['_time_us']=int(m[1]);events.append(v)
 configs=[v for v in events if v['event']=='configured'];assert len(configs)==4 and {v['node'] for v in configs}=={0,1,2,3};config={k:configs[0][k] for k in ['mode','proof','attack','timing']};assert all(all(v[k]==val for k,val in config.items()) for v in configs)
 ledger=FeedbackLedger(4,MODES[config['mode']]);pub=Ed25519PrivateKey.from_private_bytes(bytes(range(1,33))).public_key();offers={};sink={};receipt={};txs=set();rxs=[];decisions=[];obslist=[];masks=[];logitslist=[];maxfeatures=0;credits=0;proof_acks=set();snapshots=0;rejects=collections.Counter();passives=0;finals=[];wirekind=collections.Counter();wirebytes=0
 def key(a,b):return bytes((17*i+13*min(a,b)+7*max(a,b))%256 for i in range(32))
 def checkwire(v):
  w=bytes.fromhex(v['wire']);version,kind,src,dst,session,seq,n=HEADER.unpack(w[:20]);assert version==1 and kind in [1,2,3,4] and len(w)==n+36 and session==1000+src
  assert hmac.compare_digest(w[-16:],hmac.digest(key(src,dst),DOMAIN+w[:-16],'sha256')[:16])
  if kind==2:
   d=Datagram.decode(w[20:-16]);assert hmac.compare_digest(d.source_tag,hmac.digest(key(d.source,3),SOURCE+d.immutable(),'sha256')[:16])
  elif kind==3:pub.verify(w[34:-16],SINK+w[20:34])
  return w,kind,src,dst
 for v in events:
  node=v['_node'];event=v['event']
  if event in ['local_tx','cooja_rx','cooja_passive']:
   w,kind,src,dst=checkwire(v)
   if event=='local_tx':
    assert src==node and dst==v['peer'];txs.add(v['wire']);wirekind[kind]+=1;wirebytes+=len(w)
    if kind==4:assert config['proof'] and (src,int.from_bytes(w[22:26],'big')) in proof_acks
   else:
    assert v['wire'] in txs
    if event=='cooja_rx':assert dst==node and src==v['peer'];rxs.append((node,kind,int.from_bytes(w[22:26],'big') if kind!=1 else -1))
    else:assert dst!=node and src==v['peer'] and math.dist(XY[node],XY[src])<=50.0001;passives+=1
  elif event=='cooja_ack':
   if v['ok'] and v['kind']==2:proof_acks.add((node,v['pid']))
  elif event=='feedback':
   t=v['now_ms']/1000;observer=v['node'];peer=v['peer'];pid=v['pid'];op=v['op']
   if op=='register':ledger.register(observer,peer,pid,t,v['expected'])
   elif op=='ack':ledger.acknowledge(observer,peer,pid,bool(v['ok']),t)
   elif op=='evidence':ledger.evidence(observer,peer,pid,v['kind'],t)
   elif op=='expire':ledger.expire(t+1e-9)
   else:raise AssertionError(op)
   watch=ledger.watches[(observer,peer,pid)]
   assert abs(ledger.risk[observer].a[peer]-v['a'])<2e-4 and abs(ledger.risk[observer].b[peer]-v['b'])<2e-4,(folder,node,pid,op,ledger.risk[observer].a[peer],v['a'])
   assert abs(watch.seen-v['seen'])<1e-6 and abs(watch.credited-v['credited'])<1e-6;credits+=1
  elif event=='feedback_snapshot':
   assert np.allclose(v['a'],ledger.risk[node].a,atol=2e-4) and np.allclose(v['b'],ledger.risk[node].b,atol=2e-4);snapshots+=1
  elif event=='local_decision':
   obs=np.array(struct.unpack('!93f',bytes.fromhex(v['obs_hex'])),np.float32);ref,ids=features(v,node,ledger);err=float(np.max(abs(obs-ref)));maxfeatures=max(maxfeatures,err);assert err<1e-4,(folder,node,v['pid'],err,ids,v['ids']);assert ids==v['ids'];mask=np.zeros(8,bool);mask[:len(ids)]=1;obslist.append(obs);masks.append(mask);logitslist.append(np.array(struct.unpack('!8f',bytes.fromhex(v['logits_hex']))));decisions.append(v)
  elif event=='cooja_offer':assert v['pid'] not in offers;offers[v['pid']]=v['now_ms']
  elif event=='local_sink_delivery':assert node==3 and v['pid'] not in sink;sink[v['pid']]=v['now_ms']
  elif event=='local_receipt' and node==0:assert v['pid'] not in receipt;receipt[v['pid']]=v['now_ms']
  elif event=='cooja_final':finals.append(v)
  elif event=='reject':rejects[v['reason']]+=1
 assert set(offers)==set(range(60)) and len(finals)==4 and {v['node'] for v in finals}=={0,1,2,3};assert set(receipt)<=set(sink)<=set(offers);assert decisions and len(decisions)==snapshots
 assert not any(v['tx_queue_overflows'] or v['rx_queue_overflows'] for v in finals),'Application queue overflow'
 assert next(v['delivered'] for v in finals if v['node']==3)==len(sink);assert next(v['receipts'] for v in finals if v['node']==0)==len(receipt)
 if _MODEL is None:_MODEL=load_policy(r/'outputs/jicce_validation/checkpoints/attention_41001.pt','attention');torch.set_num_threads(1)
 with torch.no_grad():ref_logits,_,_=_MODEL(torch.tensor(np.array(obslist)),torch.tensor(np.array(masks)))
 maxlogit=0
 for v,expected,actual,mask in zip(decisions,ref_logits.numpy(),logitslist,masks):
  maxlogit=max(maxlogit,float(np.max(abs(expected[mask]-actual[mask]))));assert v['peer']==v['ids'][int(expected.argmax())]
 assert maxlogit<1e-4
 critical=[pid for pid in offers if pid%3==0];deadline=[90,350,1500]
 late=sum(pid not in sink or sink[pid]-offers[pid]>90 for pid in critical);source_late=sum(pid not in receipt or receipt[pid]-offers[pid]>deadline[pid%3] for pid in offers)
 energy=[]
 for v in finals:
  assert v['tx']+v['listen']==v['cpu']+v['lpm'];energy.append({'node':v['node'],'tx_s':v['tx']/v['hz'],'listen_s':v['listen']/v['hz']})
 return dict(status='independent_audit_passed',config=config,offered=60,delivered=len(sink),source_receipts=len(receipt),delivery=len(sink)/60,critical_sink_deadline_failure=late/len(critical),source_missing_or_late=source_late,policy_decisions=len(decisions),multiple_choices=sum(len(v['ids'])>1 for v in decisions),max_feature_error=maxfeatures,max_logit_error=maxlogit,feedback_events_replayed=credits,passive_frames_observed=passives,transmitted_application_frames=dict(wirekind),transmitted_application_bytes=wirebytes,total_tx_state_s=sum(v['tx_s'] for v in energy),radio_state_seconds=energy,actual_mac_transmissions=sum(v['mac_attempts'] for v in finals),mac_failures=sum(v['mac_failures'] for v in finals),rejects=dict(rejects),source_receipt_delays_ms=[receipt[pid]-offers[pid] for pid in sorted(receipt)],physical_energy_measured=False,checkpoint_sha256=hashlib.sha256((r/'outputs/jicce_validation/checkpoints/attention_41001.pt').read_bytes()).hexdigest(),log_sha256=hashlib.sha256(raw).hexdigest())

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();d=audit_run(a.run);(a.run/'audit.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))

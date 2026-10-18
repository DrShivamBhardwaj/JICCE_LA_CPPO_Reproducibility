"""Deterministic post-freeze diagnostics; not routing performance experiments."""
import json,sys,platform,subprocess,importlib.metadata,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from wsn_sim.bounded_feedback import BoundedFeedbackLedger
from wsn_sim.censored_feedback import FeedbackLedger
from wsn_sim.distributed_auth import Node,Channel
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
root=Path(__file__).resolve().parents[1];out=root/"outputs/validation_20261018";out.mkdir(parents=True,exist_ok=True)
ledger=BoundedFeedbackLedger(2,capacity=128,history_capacity=64)
peak=0
for pid in range(100000):
    t=pid*.01
    if ledger.register(0,1,pid,t,.04):
        ledger.acknowledge(0,1,pid,True,t)
        ledger.evidence(0,1,pid,"passive",t)
        ledger.evidence(0,1,pid,"receipt",t)
    peak=max(peak,len(ledger.watches))
ledger.expire(1002.)
clock=[]
secret=Ed25519PrivateKey.from_private_bytes(bytes([42])*32);key=bytes([23])*32
for offset in [-.02,-.005,0.,.005,.02]:
 for drift_ppm in [-50,0,50]:
  for physical_time in [1.,60.,300.]:
   sender=Node(0,(0,0),1,(30,0),Channel(0,100,{1:key},{1:101}),secret.public_key())
   receiver=Node(1,(30,0),1,(30,0),Channel(1,101,{0:key},{0:100}),secret.public_key(),secret)
   sender_time=physical_time*(1+drift_ppm*1e-6)+offset
   _,wire=sender.beacon(1,1.,0,sender_time)
   receiver.receive(wire,0,physical_time+.001)
   clock.append(dict(offset_s=offset,drift_ppm=drift_ppm,physical_time_s=physical_time,received=0 in receiver.cache,rejections=receiver.rejects))
credit=[]
for q in [0.,.001,.04,.099,.5,1.]:
 for cls in [FeedbackLedger,BoundedFeedbackLedger]:
  values=[]
  for split in [False,True]:
   l=cls(2,"censored") if cls is FeedbackLedger else cls(2)
   l.register(0,1,1,0.,q);l.acknowledge(0,1,1,True,.01)
   if split:l.evidence(0,1,1,"passive",.02)
   l.evidence(0,1,1,"receipt",.03);values.append(float(l.risk[0].a[1]-1))
  credit.append(dict(q=q,implementation=cls.__name__,whole_credit=values[0],split_credit=values[1]))
sources=["src/wsn_sim/censored_feedback.py","src/wsn_sim/bounded_feedback.py","src/wsn_sim/distributed_auth.py"]
result=dict(base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),platform=platform.platform(),python=sys.version,dependencies={p:importlib.metadata.version(p) for p in ["numpy","torch","pytest","cryptography"]},source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},stream=dict(events=100000,capacity=128,peak_watches=peak,final_watches=len(ledger.watches),retired=ledger.retired,capacity_rejections=ledger.capacity_rejections,history_size=len(ledger.updates),history_capacity=64),credit=credit,independent_clock_beacon_cases=clock,clock_summary=dict(cases=len(clock),accepted=sum(c["received"] for c in clock),rejected=sum(not c["received"] for c in clock)),scope="Unit and deterministic diagnostic evidence only; no new routing gain, MCU execution, physical RF or measured energy claim")
(out/"diagnostics.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["stream","clock_summary","scope"]},indent=2))

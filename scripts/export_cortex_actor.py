"""Export frozen actor weights and retained radio observations for a C harness."""
from pathlib import Path
import sys,json,gzip,hashlib,hmac,struct
import numpy as np,torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/"src"))
from wsn_sim.rl import LocalAttentionActorCritic
out=r/"hardware/cortex_m3_validation/generated";out.mkdir(parents=True,exist_ok=True)
cp=r/"outputs/jicce_validation/checkpoints/attention_41001.pt"
w=torch.load(cp,map_location="cpu",weights_only=True);model=LocalAttentionActorCritic(13,10,8,hidden=96,n_costs=6);model.load_state_dict(w);model.eval()
trace=r/"outputs/ns3_censored/trace_77001.jsonl.gz";cases=[]
with gzip.open(trace,"rt") as h:
 for line in h:
  d=json.loads(line)
  if d.get("type")=="decision" and d.get("arm")=="censored_passive":
   cases.append(d)
   if len(cases)==16:break
assert len(cases)==16
base=cases[:8]
cases=[dict(c,validation_kind="retained_radio_decision",permutation=list(range(8))) for c in base]
for shift,c in enumerate(base):
 perm=np.roll(np.arange(8),shift).tolist();obs=np.asarray(c["obs"],dtype=float)
 transformed=np.concatenate([obs[:13],obs[13:].reshape(8,10)[perm].ravel()]).tolist()
 cases.append(dict(c,obs=transformed,mask=np.asarray(c["mask"])[perm].tolist(),validation_kind="candidate_permutation_control",permutation=perm))
def name(s):return s.replace(".","_")
def floats(a):return ",".join(float(x).hex()+"f" for x in np.asarray(a).ravel())
names=[k for k in w if not k.startswith(("critic.","value.","cost_values."))]
assert sum(w[k].numel() for k in names)==44161
parts=["/* Generated from frozen checkpoint. Do not edit. */"]
for k in names:
 a=w[k].numpy();parts.append(f"static const float {name(k)}[{a.size}]={{"+floats(a)+"};")
parts.append("static const float observations[16][93]={"+",".join("{"+floats(c["obs"])+"}" for c in cases)+"};")
parts.append("static const unsigned char masks[16][8]={"+",".join("{"+",".join(str(int(v)) for v in c["mask"])+"}" for c in cases)+"};")
private=Ed25519PrivateKey.from_private_bytes(bytes([42])*32)
msg=b"JICCE-sink-v1\0"+struct.pack("!HIQ",0,7,100)
signature=private.sign(msg)
key=bytes([11])*20;data=b"Hi There";digest=hmac.digest(key,data,"sha256")
for k,b in [("test_seed",bytes([42])*32),("test_message",msg),("test_signature",signature),("test_public",private.public_key().public_bytes_raw()),("hmac_key",key),("hmac_message",data),("hmac_expected",digest)]:
 parts.append(f"static const unsigned char {k}[{len(b)}]={{"+",".join(map(str,b))+"};")
(out/"actor_vectors.h").write_text("\n".join(parts)+"\n")
references=[]
with torch.no_grad():
 for c in cases:
  logit,_,_=model(torch.tensor(c["obs"],dtype=torch.float32)[None],torch.tensor(c["mask"],dtype=torch.bool)[None])
  references.append(dict(pid=c["pid"],node=c["node"],validation_kind=c["validation_kind"],permutation=c["permutation"],logits=logit[0].tolist(),action=int(logit.argmax())))
(out/"reference.json").write_text(json.dumps(dict(checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),actor_parameters=44161,cases=references),indent=2)+"\n")
print("Exported 44,161 actor weights and eight retained decisions and eight candidate-permutation controls")

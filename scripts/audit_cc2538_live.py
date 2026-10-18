"""Audit any supplied live-pilot run directly from captures, without Renode."""
from pathlib import Path
import argparse,subprocess,socket,time,json,sys,hashlib,struct,hmac,math
import numpy as np
import torch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'src'))
from wsn_sim.auth_policy import load_policy,observation
from wsn_sim.distributed_auth import HEADER,DOMAIN,SOURCE,SINK,Datagram
def audit_run(out,expected_packets=10,topology='chain'):
 from types import SimpleNamespace
 out=Path(out);a=SimpleNamespace(packets=expected_packets,topology=topology)
 report=json.loads((out/'verification.json').read_text())
 image=r/'outputs/cc2538_live/firmware.elf'
 if report.get('elf_sha256') and report['elf_sha256']!=hashlib.sha256(image.read_bytes()).hexdigest():raise ValueError('Capture ELF identity mismatch')
 if report.get('expected_packets',expected_packets)!=expected_packets:raise ValueError('Expected packet criterion mismatch')
 xy=[(0,0),(30,0),(60,0),(90,0)] if topology=='chain' else [(0,0),(45,0),(45,20),(90,0)]
 def records(i):
  return [json.loads(l) for l in (out/f'uart_{i}.jsonl').read_text().splitlines() if l.startswith('{') and l.endswith('}')]
 all_records=[records(i) for i in range(4)];pub=Ed25519PrivateKey.from_private_bytes(bytes([42])*32).public_key();wire_count=0;decision_count=0;errors=[];feature_errors=[];multi=0
 model=load_policy(r/'outputs/jicce_validation/checkpoints/attention_41001.pt','attention');torch.set_num_threads(1)
 for node,rs in enumerate(all_records):
  for v in rs:
   if v['event']=='local_tx':
    assert any(x['event']=='rx' and x['peer']==node and x['wire']==v['wire'] for x in all_records[v['peer']]);w=bytes.fromhex(v['wire']);version,kind,src,dst,session,seq,n=HEADER.unpack(w[:20]);assert src==node and dst==v['peer'] and len(w)==36+n and session==1000+src
    key=bytes([17+min(src,dst)*4+max(src,dst)])*32;assert hmac.compare_digest(w[-16:],hmac.digest(key,DOMAIN+w[:-16],'sha256')[:16]);wire_count+=1
    if kind==2:
     d=Datagram.decode(w[20:-16]);key=bytes([17+min(d.source,3)*4+max(d.source,3)])*32
     assert hmac.compare_digest(d.source_tag,hmac.digest(key,SOURCE+d.immutable(),'sha256')[:16])
    if kind==3:pub.verify(w[34:-16],SINK+w[20:34])
   if v['event']=='local_decision':
    obs=np.array(struct.unpack('!93f',bytes.fromhex(v['obs_hex'])),dtype=np.float32);mask=np.zeros(8,dtype=bool);mask[:len(v['ids'])]=True
    c=np.array(struct.unpack('!44f',bytes.fromhex(v['cache_hex']))).reshape(4,11)
    state=dict(own=[1.,0.],xy=xy[node],sink=3,sink_xy=[90,0],now=v['now_ms']/1000,packet=dict(traffic=v['traffic'],created_us=v['created_ms']*1000,visited=v['visited']),qos_debts=struct.unpack('!6f',bytes.fromhex(v['qos_hex'])),cache={str(i):row[:5].tolist() for i,row in enumerate(c) if row[10]},links={str(i):row[6:9].tolist() for i,row in enumerate(c)},lqi={str(i):float(row[5]) for i,row in enumerate(c)},successes={str(i):int(row[9]) for i,row in enumerate(c)})
    ref_obs,ref_mask,ref_ids=observation(state);assert np.array_equal(mask,ref_mask) and v['ids']==ref_ids[:len(v['ids'])]
    feature_errors.extend(abs(obs-ref_obs));assert np.max(abs(obs-ref_obs))<1e-4
    with torch.no_grad():logits,_,_=model(torch.tensor(obs)[None],torch.tensor(mask)[None])
    expected=logits[0].numpy();actual=np.array(struct.unpack('!8f',bytes.fromhex(v['logits_hex'])))
    errors.extend(abs(expected[mask]-actual[mask]));assert v['peer']==v['ids'][int(expected.argmax())];decision_count+=1;multi+=int(mask.sum()>1)
 source={v['pid'] for v in all_records[0] if v['event']=='local_receipt'};sink=[v['pid'] for v in all_records[3] if v['event']=='local_sink_delivery'];assert sum(v['event']=='local_receipt' for v in all_records[0])==a.packets;assert source==set(range(a.packets)) and sorted(sink)==list(range(a.packets))
 reasons=[v['reason'] for rs in all_records for v in rs if v['event']=='reject'];assert sorted(reasons)==['replay','sink_signature','source_tag','tag'];assert max(errors)<1e-4
 source_created={v['pid']:v['created_ms'] for v in all_records[0] if v['event']=='local_decision'}
 delays=[dict(pid=v['pid'],traffic=v['pid']%3,receipt_delay_ms=v['now_ms']-source_created[v['pid']]) for v in all_records[0] if v['event']=='local_receipt']
 report.update(status='passed',topology=a.topology,coordinates=xy,emulated_receipt_delays=delays,timing_scope='Renode 1 MHz SysTick; not physical timing',expected_packets=a.packets,unique_sink_deliveries=len(sink),unique_source_verified_receipts=len(source),mcu_policy_decisions=decision_count,multiple_choice_decisions=multi,all_next_hops_match_frozen_host_actor=True,max_logit_error=float(max(errors)),max_feature_error=float(max(feature_errors)),host_negative_control_sealing=True,independently_authenticated_wire_records=wire_count,rejection_controls=reasons,elf_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),scope='Four-node emulated live routing/authentication pilot; explicit packet count acceptance. No physical RF/energy, reboot-safe sessions, complete 104-node protocol equivalence or statistical performance claim.')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--topology',choices=['chain','choice'],required=True);p.add_argument('--expected-packets',type=int,default=10);a=p.parse_args()
 report=audit_run(a.run,a.expected_packets,a.topology)
 (a.run/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='emulated_receipt_delays'},indent=2))

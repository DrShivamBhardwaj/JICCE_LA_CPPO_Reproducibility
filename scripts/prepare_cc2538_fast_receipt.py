"""Experimental private fast receipt plus retained deferred Ed25519 proof.
This changes the source service endpoint; it is not the original signed deadline.
"""
from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'hardware/cc2538_q22/local.h').read_text()
s=s.replace('static unsigned live_tx_counter=10000;', 'static unsigned live_tx_counter=10000;static unsigned fast_seen[16];\nstatic const uint8_t fast_domain[]="JICCE-fast-sink-v1";')
s=s.replace('kind>3||sender', 'kind>4||sender')
s=s.replace('pending_live[slot].used=1;', 'fast_seen[slot]=0;pending_live[slot].used=1;')
a=s.index('  uint8_t receipt[78],msg[28];')
s=s[:a]+'''  delivered_count++;event("local_sink_delivery",pid,sender);
  uint8_t fast[30];memcpy(fast,body,14);mac(tag,source,fast_domain,sizeof fast_domain,fast,14);memcpy(fast+14,tag,16);send_wire(4,sender,fast,30,pid);
'''+s[a:]
s=s.replace('profile("sign",sign_start);delivered_count++;event("local_sink_delivery",pid,sender);send_wire', 'profile("sign",sign_start);send_wire')
anchor=' if(size!=78){reject("receipt_length");return;}'
extra=''' if(kind==4){
  if(size!=30||u16(body)!=0){reject("fast_length_source");return;}
  if(node_id==0){mac(tag,3,fast_domain,sizeof fast_domain,body,14);if(!equal(tag,body+14,16)){reject("fast_sink_tag");return;}}
  for(unsigned i=0;i<16;i++)if(pending_live[i].used&&pending_live[i].source==u16(body)&&pending_live[i].pid==u32(body+2)&&pending_live[i].session==u64(body+6)){
   if(pending_live[i].peer!=sender||fast_seen[i]){reject("fast_route_duplicate");return;}fast_seen[i]=1;
   if(node_id==0){settle_live(i,1);event("local_fast_receipt",u32(body+2),sender);}
   else send_wire(4,pending_live[i].previous,body,30,u32(body+2));
   /* No positive forwarding credit is assigned from this opaque relay proof. */
   return;
  }
  reject("fast_route");return;
 }
'''
assert anchor in s;s=s.replace(anchor,extra+anchor)
(r/'hardware/cc2538_q22/local_fast.h').write_text(s)
s=(r/'scripts/build_cc2538_q22.py').read_text().replace("'outputs/cc2538_q22'","'outputs/cc2538_fast'").replace("'hardware/cc2538_q22/local.h'","'hardware/cc2538_q22/local_fast.h'")
(r/'scripts/build_cc2538_fast.py').write_text(s)
s=(r/'scripts/run_cc2538_q22.py').read_text().replace('outputs/cc2538_q22','outputs/cc2538_fast').replace('from audit_cc2538_q22 import audit_run','from audit_cc2538_fast import audit_run')
anchor="  for i in range(4):issue(i,dict(command='local_status'))"
extra='''  v=next(v for v in reversed(rs[original['peer']]) if v['event']=='local_tx' and bytes.fromhex(v['wire'])[1]==4 and v['peer']==0)
  body=bytearray.fromhex(v['wire'])[20:-16];body[-1]^=1
  inject_authenticated(original['peer'],0,v['wire'],100002,body)
'''
assert anchor in s;s=s.replace(anchor,extra+anchor)
(r/'scripts/run_cc2538_fast.py').write_text(s)
s=(r/'scripts/audit_cc2538_q22.py').read_text().replace('outputs/cc2538_q22','outputs/cc2538_fast')
s=s.replace("if kind==3:pub.verify(w[34:-16],SINK+w[20:34])", "if kind==3:pub.verify(w[34:-16],SINK+w[20:34])\n    if kind==4:\n     assert n==30 and int.from_bytes(w[20:22],'big')==0\n     assert hmac.compare_digest(w[34:50],hmac.digest(pair_key(0,3),b'JICCE-fast-sink-v1\\0'+w[20:34],'sha256')[:16])")
s=s.replace("['provision_key_mismatch','replay','reprovision','session','sink_signature','source_tag','tag']", "['fast_sink_tag','provision_key_mismatch','replay','reprovision','session','sink_signature','source_tag','tag']")
anchor=" report.update(status='passed'"
extra=''' fast_rows=[v for v in all_records[0] if v['event']=='local_fast_receipt'];assert len(fast_rows)==a.packets and {v['pid'] for v in fast_rows}==set(range(a.packets))
 fast_delays=[dict(pid=v['pid'],traffic=v['pid']%3,receipt_delay_ms=v['now_ms']-source_created[v['pid']]) for v in fast_rows]
 report.update(fast_source_receipt_delays=fast_delays,fast_receipt_guarantee='Source/sink HMAC authentication, not a public signature; relays forward opaquely without credit; original Ed25519 proof is retained and independently verified',extra_application_frame_kind=4)
'''
assert anchor in s;s=s.replace(anchor,extra+anchor)
(r/'scripts/audit_cc2538_fast.py').write_text(s)

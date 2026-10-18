"""Generate an explicitly separate Cooja policy/feedback port from retained MCU code."""
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'hardware/cooja_feedback';d.mkdir(exist_ok=True)
s=(r/'hardware/cc2538_q22/local.h').read_text()
s=s.replace(' unsigned lo=node_id<peer?node_id:peer,hi=node_id<peer?peer:node_id;','')
s=s.replace('kind>3','kind>4')
s=s.replace('uint8_t body[78];memcpy(body,wire+20,size);','''uint8_t body[78];memcpy(body,wire+20,size);
 if(kind==4){if(size!=14){reject("proof_size");return;}feedback_evidence(u32(body+2),sender,1.f,"proof");return;}
 if(kind==2&&attack_enabled&&node_id==1&&u32(body+2)>=20){event("app_blackhole",u32(body+2),sender);return;}''')
s=s.replace('static unsigned live_tx_counter=10000;','static unsigned live_tx_counter=10000;\n'+(d/'feedback_ledger.h').read_text())
a=s.index('static void local_ack(');b=s.index('static void forward_live(',a)
s=s[:a]+'''static void local_ack(unsigned token,int ok){
 if(!local_enabled)return;
 for(unsigned i=0;i<16;i++)if(pending_live[i].used&&pending_live[i].token==token){
  unsigned p=pending_live[i].peer;pending_live[i].acked=ok!=0;cache[p].a+=(float)(ok!=0);cache[p].b+=(float)(ok==0);
  cache[p].delay=.8f*cache[p].delay+.2f*(milliseconds-pending_live[i].sent)*.001f;
  feedback_ack(i,ok);event(ok?"local_mac_ok":"local_mac_failed",pending_live[i].pid,p);
  if(ok&&proof_enabled&&pending_live[i].previous!=65535){uint8_t proof[14];w16(proof,pending_live[i].source);w32(proof+2,pending_live[i].pid);w64(proof+6,pending_live[i].session);send_wire(4,pending_live[i].previous,proof,14,pending_live[i].pid);}
  break;
 }
}
''' + s[b:]
s=s.replace('ta=1+cache[p].success*pdr,risk=.75f/(ta+1),ucb=clip(risk+1.645f*.75f*sqroot(ta/((ta+1)*(ta+1)*(ta+2))),0,1);','ta=feedback_a[p],tb=feedback_b[p],risk=.75f*tb/(ta+tb),ucb=clip(risk+1.645f*.75f*sqroot(ta*tb/((ta+tb)*(ta+tb)*(ta+tb+1))),0,1);')
s=s.replace('pending_live[slot].token=send_wire(2,peer,body,n,pid);','feedback_register(slot,peer,pid,cache[peer].a/(cache[peer].a+cache[peer].b));\n pending_live[slot].token=send_wire(2,peer,body,n,pid);')
s=s.replace('if(pending_live[i].acked&&!pending_live[i].credited){cache[sender].success++;pending_live[i].credited=1;}','feedback_evidence(u32(body+2),sender,1.f,"receipt");')
s=s.replace('delivered_count++;event("local_sink_delivery",pid,sender);send_wire(3,sender,receipt,78,pid);','delivered_count++;event("local_sink_delivery",pid,sender);send_wire(3,sender,receipt,78,pid);')
s=s.replace('static void local_expire(void){for','static void local_expire(void){feedback_expire();for')
# Log weighted counts beside the exact local observation and actor logits.
s=s.replace('text("{\\"event\\":\\"local_decision\\",\\"pid\\":");','feedback_snapshot();text("{\\"event\\":\\"local_decision\\",\\"pid\\":");')
assert 'feedback_snapshot();text' in s
# Prior function declarations required by the inserted ledger block.
s=s.replace('static unsigned live_tx_counter=10000;','static float clip(float,float,float);\nstatic unsigned live_tx_counter=10000;')
(d/'local_feedback.h').write_text(s)
print(d/'local_feedback.h')

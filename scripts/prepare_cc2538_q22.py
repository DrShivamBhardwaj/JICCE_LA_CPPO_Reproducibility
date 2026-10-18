"""Generate a faster declared actor approximation and software key hygiene."""
from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'hardware/cc2538_live/local_profile.h').read_text()
s=s.replace('static unsigned provisioned;', 'static unsigned provisioned;static uint8_t sink_secret_cached[64];')
s=s.replace('static uint64_t pair_session', 'static void secret_wipe(void*p,unsigned n){volatile uint8_t*x=p;while(n--)*x++=0;}\nstatic uint64_t pair_session')
s=s.replace('profile("hmac",started);','secret_wipe(block,sizeof block);secret_wipe(inner,sizeof inner);secret_wipe(&c,sizeof c);profile("hmac",started);')
s=s.replace('profile("actor",actor_start);','profile("actor",actor_start);if(selected<0){reject("actor_input_bounds");return;}')
a=s.index('  uint8_t receipt[78],msg[28],seed[32]');b=s.index('delivered_count++;',a)
s=s[:a]+'''  uint8_t receipt[78],msg[28];memcpy(receipt,body,14);memcpy(msg,sink_domain,sizeof sink_domain);memcpy(msg+sizeof sink_domain,receipt,14);
  unsigned sign_start=milliseconds;crypto_ed25519_sign(receipt+14,sink_secret_cached,msg,sizeof sink_domain+14);profile("sign",sign_start);''' +s[b:]
s=s.replace('provisioned=1;memset(data,0,sizeof data);', '''if(node_id==3){uint8_t public_check[32];crypto_ed25519_key_pair(sink_secret_cached,public_check,sink_seed);if(!equal(public_check,sink_pub,32)){secret_wipe(data,sizeof data);secret_wipe(provision_keys,sizeof provision_keys);secret_wipe(sink_secret_cached,sizeof sink_secret_cached);reject("provision_key_mismatch");return 1;}}
  secret_wipe(sink_seed,sizeof sink_seed);provisioned=1;secret_wipe(data,sizeof data);''')
(r/'hardware/cc2538_q22/local.h').write_text(s)
s=(r/'scripts/build_cc2538_profile.py').read_text().replace("'outputs/cc2538_profile'","'outputs/cc2538_q22'").replace("'hardware/cc2538_live/local_profile.h'","'hardware/cc2538_q22/local.h'")
a=s.index("functions=functions.replace(");b=s.index("pre='''",a)
s=s[:a]+"fa=functions.index('static float fast_tanh');fb=functions.index('static void hmac_sha256',fa);functions=functions[:fa]+'#include \\\"actor.h\\\"\\n'+functions[fb:]\n".replace('\\\"','"')+s[b:]
s=s.replace("'-I'+str(d/'include'),", "'-I'+str(r/'hardware/cc2538_q22'),'-I'+str(d/'include'),")
# Wipe the UART command buffer after each complete command; incoming provisioning is never echoed.
s=s.replace("source=out/'firmware.c';", "s=s.replace('used=0;overflow=0;}', 'secret_wipe(line,sizeof line);used=0;overflow=0;}')\nsource=out/'firmware.c';")
(r/'scripts/build_cc2538_q22.py').write_text(s)
s=(r/'scripts/run_cc2538_profile.py').read_text().replace('outputs/cc2538_profile','outputs/cc2538_q22').replace('from audit_cc2538_profile import audit_run','from audit_cc2538_q22 import audit_run')
# Exercise key/public mismatch before the successful provisioning, without printing material.
anchor='  for i in range(4):\n   material='
extra='''  bad_material=b''.join(pair_key(3,j) if j!=3 else bytes(32) for j in range(4))+bytes(32)+sink_pub+b''.join(struct.pack('!Q',x) for x in sessions)
  issue(3,dict(command='provision_material',material=bad_material.hex()))
  wait(lambda:any(v['event']=='reject' and v['reason']=='provision_key_mismatch' for v in records(3)),'signing key mismatch rejection')
'''
assert anchor in s;s=s.replace(anchor,extra+anchor)
(r/'scripts/run_cc2538_q22.py').write_text(s)
s=(r/'scripts/audit_cc2538_profile.py').read_text().replace('outputs/cc2538_profile','outputs/cc2538_q22').replace("['replay','reprovision','session','sink_signature','source_tag','tag']", "['provision_key_mismatch','replay','reprovision','session','sink_signature','source_tag','tag']")
s=s.replace("all_next_hops_match_frozen_host_actor=True", "all_next_hops_match_frozen_host_actor=True,actor_arithmetic='Q22 approximation; 8193-point tanh LUT; bounded input cube ±32'")
(r/'scripts/audit_cc2538_q22.py').write_text(s)

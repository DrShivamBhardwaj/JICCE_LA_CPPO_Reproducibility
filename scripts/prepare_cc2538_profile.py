"""Add emulated stage timing without changing packet authentication semantics."""
from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'hardware/cc2538_live/local_v2.h').read_text()
anchor='static void mac('
profile='''static void profile(const char*stage,unsigned start){text("{\\\"event\\\":\\\"stage_time\\\",\\\"node\\\":");number(node_id);text(",\\\"stage\\\":\\\"");text(stage);text("\\\",\\\"elapsed_ms\\\":");number(milliseconds-start);text("}\\n");}
'''
s=s.replace(anchor,profile+anchor)
s=s.replace('uint8_t block[64]={0},inner[32];SHA256_CTX c;','unsigned started=milliseconds;uint8_t block[64]={0},inner[32];SHA256_CTX c;')
s=s.replace('sha256_update(&c,inner,32);sha256_final(&c,out);','sha256_update(&c,inner,32);sha256_final(&c,out);profile("hmac",started);')
s=s.replace('float logits[8];int selected=mode_attention?actor(obs,mask,logits):0;','unsigned actor_start=milliseconds;float logits[8];int selected=mode_attention?actor(obs,mask,logits):0;profile("actor",actor_start);')
s=s.replace('crypto_ed25519_key_pair(secret,pub,seed);crypto_ed25519_sign(receipt+14,secret,msg,sizeof sink_domain+14);','unsigned key_start=milliseconds;crypto_ed25519_key_pair(secret,pub,seed);profile("key_pair",key_start);unsigned sign_start=milliseconds;crypto_ed25519_sign(receipt+14,secret,msg,sizeof sink_domain+14);profile("sign",sign_start);')
s=s.replace('if(crypto_ed25519_check(body+14,sink_pub,msg,sizeof sink_domain+14)){', 'unsigned verify_start=milliseconds;int verify_result=crypto_ed25519_check(body+14,sink_pub,msg,sizeof sink_domain+14);profile("verify",verify_start);if(verify_result){')
(r/'hardware/cc2538_live/local_profile.h').write_text(s)
s=(r/'scripts/build_cc2538_v2.py').read_text().replace("'outputs/cc2538_v2'","'outputs/cc2538_profile'").replace("'hardware/cc2538_live/local_v2.h'","'hardware/cc2538_live/local_profile.h'")
(r/'scripts/build_cc2538_profile.py').write_text(s)
s=(r/'scripts/run_cc2538_v2.py').read_text().replace("'outputs/cc2538_v2'","'outputs/cc2538_profile'").replace('outputs/cc2538_v2/firmware.elf','outputs/cc2538_profile/firmware.elf').replace('from audit_cc2538_v2 import audit_run','from audit_cc2538_profile import audit_run')
s=s.replace("(out.name+'.private.json')","(out.parent.name+'_'+out.name+'_'+uuid.uuid4().hex[:8]+'.private.json')")
(r/'scripts/run_cc2538_profile.py').write_text(s)
s=(r/'scripts/audit_cc2538_v2.py').read_text().replace('outputs/cc2538_v2/firmware.elf','outputs/cc2538_profile/firmware.elf')
(r/'scripts/audit_cc2538_profile.py').write_text(s)

"""Generate the separately scoped provisioning/long-stream firmware source."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/'hardware/cc2538_live/local.h').read_text()
s=s.replace('static unsigned pair_session(unsigned n){return 1000u+n;}', 'static uint8_t provision_keys[4][32],sink_seed[32],sink_pub[32];static uint64_t boot_sessions[4];static unsigned provisioned;\nstatic uint64_t pair_session(unsigned n){return boot_sessions[n];}')
s=s.replace('for(unsigned i=0;i<32;i++)block[i]=(uint8_t)(17+lo*4+hi); /* public deterministic TEST key */','for(unsigned i=0;i<32;i++)block[i]=provision_keys[peer][i];')
s=s.replace('for(unsigned i=0;i<32;i++)seed[i]=42;','for(unsigned i=0;i<32;i++)seed[i]=sink_seed[i];').replace('test_public,msg','sink_pub,msg')
s=s.replace('static unsigned seen_pid[16],seen_used[16];', 'static struct {unsigned seen,highest;uint64_t bits;} source_replay[4];')
a=s.index('  for(unsigned i=0;i<16;i++)if(seen_used[i]');b=s.index('  uint8_t receipt[78]',a)
s=s[:a]+'''  if(source_replay[source].seen&&pid<=source_replay[source].highest){unsigned delta=source_replay[source].highest-pid;if(delta>=64||(source_replay[source].bits&((uint64_t)1<<delta))){reject("sink_duplicate");return;}source_replay[source].bits|=(uint64_t)1<<delta;}
  else {unsigned gap=pid-source_replay[source].highest;source_replay[source].bits=(!source_replay[source].seen||gap>=64)?1:(source_replay[source].bits<<gap)|1;source_replay[source].highest=pid;source_replay[source].seen=1;}
''' +s[b:]
anchor='static int local_command(const char*s){'
provision='''
 if(find(s,"provision_material")){
  if(provisioned){reject("reprovision");return 1;}
  const char*p=field(s,"\\\"material\\\"");uint8_t data[224];unsigned n=0;
  if(!p||*p++!='\\\"'){reject("provision_format");return 1;}
  while(*p&&*p!='\\\"') {int a=digit(*p++);if(!*p||*p=='\\\"'){reject("provision_format");return 1;}int b=digit(*p++);if(a<0||b<0||n>=224){reject("provision_format");return 1;}data[n++]=(uint8_t)(16*a+b);}
  if(n!=224||*p!='\\\"'){reject("provision_format");return 1;}
  memcpy(provision_keys,data,128);memcpy(sink_seed,data+128,32);memcpy(sink_pub,data+160,32);for(unsigned i=0;i<4;i++)boot_sessions[i]=u64(data+192+8*i);
  for(unsigned i=0;i<4;i++){if(!boot_sessions[i]){reject("provision_session");return 1;}for(unsigned j=0;j<i;j++)if(boot_sessions[i]==boot_sessions[j]){reject("provision_session");return 1;}}
  provisioned=1;memset(data,0,sizeof data);event("provisioned",0,0);return 1;
 }
'''
assert anchor in s;s=s.replace(anchor,anchor+provision)
s=s.replace('if(find(s,"local_start")){if(local_enabled)', 'if(find(s,"local_start")){if(!provisioned){reject("unprovisioned");return 1;}if(local_enabled)')
s=s.replace('/* Four-node emulated live-path pilot. Public test keys only. */','/* Four-node emulated pilot with trusted UART provisioning. No production-board claim. */')
(r/'hardware/cc2538_live/local_v2.h').write_text(s)
p=r/'scripts/build_cc2538_live.py';s=p.read_text().replace("out=r/'outputs/cc2538_live'", "out=r/'outputs/cc2538_v2'").replace("'hardware/cc2538_live/local.h'","'hardware/cc2538_live/local_v2.h'").replace("'-Oz','-g'","'-O2','-fno-unroll-loops','-g'")
s=s.replace('public keys and nominal telemetry only','trusted UART provisioning and nominal telemetry')
(r/'scripts/build_cc2538_v2.py').write_text(s)

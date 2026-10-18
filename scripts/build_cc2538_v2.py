"""Compile a four-node live-path pilot; trusted UART provisioning and nominal telemetry."""
from pathlib import Path
import subprocess,re,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build';b.mkdir(exist_ok=True);d=r/'hardware/cortex_m3_validation';out=r/'outputs/cc2538_v2';out.mkdir(exist_ok=True)
h=(d/'harness.c').read_text();functions=h[h.index('static void hex32'):h.index('#ifdef MCU\nextern uint32_t _bss_end')]
functions=functions.replace('for(int v=0;v<8;v++){','for(int v=0;v<8;v++){if(!mask[v]){logit[v]=-1.e9f;continue;}')
pre='''#include <stddef.h>
#include "sha256.h"
#include "monocypher-ed25519.h"
#include "actor_vectors.h"
static void emit(const char*s){text(s);}
int memcmp(const void*a,const void*b,size_t n){const unsigned char*x=a,*y=b;for(size_t i=0;i<n;i++)if(x[i]!=y[i])return x[i]-y[i];return 0;}
'''
s=(r/'hardware/renode_cc2538/bridge.c').read_text()
s=s.replace('Host performs routing and cryptography.', 'This pilot performs live routing and cryptography on the emulated MCU.')
s=s.replace('volatile uint32_t node_id;', 'static void receive_live(const uint8_t*,unsigned,unsigned);\nstatic void local_ack(unsigned,int);\nvolatile uint32_t node_id;')
s=s.replace('static void ack(uint32_t token,int ok){','static void ack(uint32_t token,int ok){local_ack(token,ok);')
s=s.replace('for(unsigned i=9;i<len-2;i++)bytehex(frame[i]);text("\\\"}\\n");','for(unsigned i=9;i<len-2;i++)bytehex(frame[i]);text("\\\"}\\n");\n   receive_live(frame+9,len-11,peer-1);')
assert 'receive_live(frame+9' in s
local=(r/'hardware/cc2538_live/local_v2.h').read_text()
s=s.replace('static void command(const char*s){',pre+functions+local+'\nstatic void command(const char*s){\n if(local_command(s))return;')
s=s.replace('REG(0x4000c02cu)=0x60u;', 'mode_attention=1;last_pid=0xffffffffu;live_tx_counter=10000;\n REG(0x4000c02cu)=0x60u;')
s=s.replace('radio_rx();','radio_rx();local_expire();')
source=out/'firmware.c';source.write_text(s)
env=subprocess.check_output(['zig','env'],text=True);libdir=Path(re.search(r'\.lib_dir = "([^"]+)"',env).group(1))
subprocess.run(['zig','build-lib',str(libdir/'compiler_rt.zig'),'-target','thumb-freestanding-eabi','-mcpu=cortex_m3','-O','ReleaseSmall','-femit-bin='+str(b/'libcompiler_rt.a')],check=True)
cmd=['zig','cc','-target','thumb-freestanding-eabi','-mcpu=cortex_m3','-O2','-fno-unroll-loops','-g','-ffp-contract=off','-ffreestanding','-fno-builtin','-fno-stack-protector','-ffunction-sections','-fdata-sections','-nostdlib','-I'+str(d/'include'),'-I'+str(d/'vendor'),'-I'+str(d/'generated'),str(source),str(d/'vendor/sha256.c'),str(d/'vendor/monocypher.c'),str(d/'vendor/monocypher-ed25519.c'),str(b/'libcompiler_rt.a'),'-Wl,-T,'+str(r/'hardware/renode_cc2538/link.ld'),'-Wl,-e,Reset_Handler','-Wl,--gc-sections','-o',str(out/'firmware.elf')]
subprocess.run(cmd,check=True)
(out/'build.json').write_text(json.dumps(dict(command=cmd,elf_sha256=hashlib.sha256((out/'firmware.elf').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Four-node live-path emulation pilot; public test keys; no physical validation'),indent=2)+'\n')
print(out)

"""Build a CC2538 radio bridge with boot-time actor/crypto tests.

This image does NOT move the live routing/authentication loop off the host.
Original bridge.c and archived radio evidence remain unchanged.
"""
from pathlib import Path
import subprocess,re,json,hashlib
r=Path(__file__).resolve().parents[1]; b=r/'build'; b.mkdir(exist_ok=True)
d=r/'hardware/cortex_m3_validation'; out=r/'outputs/cc2538_boot_selftest';out.mkdir(exist_ok=True)
h=(d/'harness.c').read_text()
functions=h[h.index('static void hex32'):h.index('#ifdef MCU\nextern uint32_t _bss_end')]
main=h[h.index('int main(void){'):h.index('\n#ifdef MCU\nextern uint32_t _data_start')]
main=re.sub(r'#ifdef MCU\n.*?#endif\n','',main,flags=re.S).replace('int main(void)','static int cc_selftest(void)')
pre='''#include <stddef.h>
#include "sha256.h"
#include "monocypher-ed25519.h"
#include "actor_vectors.h"
static void emit(const char*s){text(s);}
static void finish(unsigned code){(void)code;}
int memcmp(const void*a,const void*b,size_t n){const unsigned char*x=a,*y=b;for(size_t i=0;i<n;i++)if(x[i]!=y[i])return x[i]-y[i];return 0;}
'''
bridge=(r/'hardware/renode_cc2538/bridge.c').read_text()
bridge=bridge.replace('static void command(const char*s){',pre+functions+main+'\nstatic void command(const char*s){')
bridge=bridge.replace('RF(0x5c8)=0x34;', 'if(cc_selftest()){text("SELFTEST_FAILED\\n");for(;;){}}\n RF(0x5c8)=0x34;')
source=out/'firmware.c';source.write_text(bridge)
env=subprocess.check_output(['zig','env'],text=True)
libdir=Path(re.search(r'\.lib_dir = "([^"]+)"',env).group(1))
subprocess.run(['zig','build-lib',str(libdir/'compiler_rt.zig'),'-target','thumb-freestanding-eabi','-mcpu=cortex_m3','-O','ReleaseSmall','-femit-bin='+str(b/'libcompiler_rt.a')],check=True)
cmd=['zig','cc','-target','thumb-freestanding-eabi','-mcpu=cortex_m3','-Oz','-g','-ffp-contract=off','-ffreestanding','-fno-builtin','-fno-stack-protector','-ffunction-sections','-fdata-sections','-nostdlib','-I'+str(d/'include'),'-I'+str(d/'vendor'),'-I'+str(d/'generated'),str(source),str(d/'vendor/sha256.c'),str(d/'vendor/monocypher.c'),str(d/'vendor/monocypher-ed25519.c'),str(b/'libcompiler_rt.a'),'-Wl,-T,'+str(r/'hardware/renode_cc2538/link.ld'),'-Wl,-e,Reset_Handler','-Wl,--gc-sections','-o',str(out/'firmware.elf')]
subprocess.run(cmd,check=True)
(out/'build.json').write_text(json.dumps(dict(command=cmd,generated_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),elf_sha256=hashlib.sha256((out/'firmware.elf').read_bytes()).hexdigest(),scope='Actor/crypto boot tests linked with radio bridge; live routing/authentication still on host',execution_verified=False),indent=2)+'\n')
print(out)

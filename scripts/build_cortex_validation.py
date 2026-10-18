"""Cross-build isolated Cortex-M3 tests with a 32 KiB SRAM linker budget."""
from pathlib import Path
import subprocess,json,hashlib,re
r=Path(__file__).resolve().parents[1];d=r/"hardware/cortex_m3_validation";shim=d/"include";shim.mkdir(exist_ok=True)
(shim/"stdlib.h").write_text("#include <stddef.h>\n")
(shim/"memory.h").write_text("#include <stddef.h>\nvoid *memcpy(void*,const void*,size_t);\nvoid *memset(void*,int,size_t);\n")
env=subprocess.check_output(["zig","env"],text=True)
libdir=Path(re.search(r'\.lib_dir = "([^"]+)"',env).group(1))
subprocess.run(["zig","build-lib",str(libdir/"compiler_rt.zig"),"-target","thumb-freestanding-eabi","-mcpu=cortex_m3","-O","ReleaseSmall","-femit-bin="+str(r/"build/libcompiler_rt.a")],check=True)
cmd=["zig","cc","-target","thumb-freestanding-eabi","-mcpu=cortex_m3","-std=c11","-Oz","-DMCU","-ffp-contract=off","-ffreestanding","-fno-builtin","-fno-stack-protector","-ffunction-sections","-fdata-sections","-nostdlib","-fuse-ld=lld","-I"+str(shim),"-I"+str(d/"vendor"),str(d/"harness.c"),str(d/"vendor/sha256.c"),str(d/"vendor/monocypher.c"),str(d/"vendor/monocypher-ed25519.c"),str(r/"build/libcompiler_rt.a"),"-Wl,-T,"+str(d/"link.ld"),"-Wl,--gc-sections","-o",str(r/"build/cortex_m3.elf")]
subprocess.run(cmd,check=True)
out=r/"outputs/validation_20261018/cortex_build.json";out.write_text(json.dumps(dict(command=cmd,elf_sha256=hashlib.sha256((r/"build/cortex_m3.elf").read_bytes()).hexdigest(),elf_bytes=(r/"build/cortex_m3.elf").stat().st_size,linker_sram_limit_bytes=32768,scope="QEMU MPS2 AN385 Cortex-M3 test image, not CC2538 board firmware"),indent=2)+"\n")
print(out)

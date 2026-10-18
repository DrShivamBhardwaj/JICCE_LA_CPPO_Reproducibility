"""Audit isolated emulated Cortex-M3 actor and cryptographic outputs."""
from pathlib import Path
import json,struct,hashlib,subprocess,shutil
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
r=Path(__file__).resolve().parents[1];d=r/"hardware/cortex_m3_validation";out=r/"outputs/validation_20261018"
ref=json.loads((d/"generated/reference.json").read_text())
text=(out/"cortex_mcu.txt").read_text();lines=text.splitlines()
rows=[x.split() for x in lines if x.startswith("ACTOR ")]
assert len(rows)==len(ref["cases"])==16
errors=[];actions=[]
for tokens,expected in zip(rows,ref["cases"]):
 assert int(tokens[2],16)==expected["action"]
 values=[struct.unpack("!f",bytes.fromhex(s))[0] for s in tokens[3:]]
 assert len(values)==8
 errors += [abs(a-b) for a,b in zip(values,expected["logits"])]
 actions.append(int(tokens[2],16))
assert max(errors)<1e-5
assert len(set(actions))==8
hmac_line=next(x.split()[1] for x in lines if x.startswith("HMAC "))
assert hmac_line=="b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"
ed=next(x.split()[1:] for x in lines if x.startswith("ED25519 "))
assert ed==["00000000","ffffffff"]
sig=bytes.fromhex(next(x.split()[1] for x in lines if x.startswith("SIGNATURE ")))
msg=b"JICCE-sink-v1\0"+struct.pack("!HIQ",0,7,100)
Ed25519PrivateKey.from_private_bytes(bytes([42])*32).public_key().verify(sig,msg)
assert any(x.strip()=="DONE 00000000" for x in lines)
ram=next(x.split()[1:] for x in lines if x.startswith("RAM "))
static,stack=[int(x,16) for x in ram];assert static+stack<32768
readelf="/opt/homebrew/opt/llvm@22/bin/llvm-readelf"
elf=r/"build/cortex_m3.elf";elf_bytes=elf.read_bytes()
assert elf_bytes[:4]==b"\x7fELF" and struct.unpack_from("<H",elf_bytes,18)[0]==40
sections=subprocess.check_output([readelf,"-h","-S","-s",str(elf)],text=True);(out/"cortex_elf_report.txt").write_text(sections)
size=subprocess.check_output(["/opt/homebrew/opt/llvm@22/bin/llvm-size",str(elf)],text=True);(out/"cortex_size.txt").write_text(size)
shutil.copy(elf,out/"cortex_m3.elf")
sources=[p for p in d.rglob("*") if p.is_file()]
report=dict(status="passed",emulator=subprocess.check_output(["qemu-system-arm","--version"],text=True).splitlines()[0],compiler=subprocess.check_output(["zig","version"],text=True).strip(),machine="mps2-an385",cpu="Cortex-M3, software floating point",cases=16,retained_radio_cases=8,permutation_controls=8,matching_actions=16,distinct_selected_indices=len(set(actions)),compared_logits=len(errors),max_logit_error=max(errors),tolerance=1e-5,hmac_rfc4231_case1=True,ed25519_sign_and_verify=True,corrupt_signature_rejected=True,empty_mask_rejected=True,static_sram_bytes=static,observed_stack_watermark_bytes=stack,linker_sram_budget_bytes=32768,linker_flash_budget_bytes=524288,elf_sha256=hashlib.sha256(elf_bytes).hexdigest(),elf_file_bytes=len(elf_bytes),reference=ref,source_sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},scope="Isolated emulated instruction-level actor and algorithm tests. No CC2538 peripheral/RF execution, integrated authenticated routing firmware, measured CPU energy or physical timing claim. Public test keys only.")
(out/"cortex_audit.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k not in ["reference","source_sha256"]},indent=2));print(size)

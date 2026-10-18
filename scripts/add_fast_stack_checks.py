"""Add tested-path stack watermarking to the separate fast profile only."""
from pathlib import Path
r=Path(__file__).resolve().parents[1];p=r/'hardware/cc2538_q22/local_fast.h';s=p.read_text()
functions=r'''extern uint32_t _bss_end;
static void stack_paint(void){uintptr_t sp;__asm__ volatile("mov %0, sp":"=r"(sp));for(volatile uint32_t*p=&_bss_end;(uintptr_t)p+64<sp;p++)*p=0xa5a5a5a5u;}
static void stack_report(void){
 volatile uint32_t*p=&_bss_end;unsigned guard=1;
 for(unsigned j=0;j<16;j++)if(p[j]!=0xa5a5a5a5u)guard=0;
 while((uintptr_t)p<0x20008000u&&*p==0xa5a5a5a5u)p++;
 text(",\"observed_stack_bytes\":");number(0x20008000u-(uintptr_t)p);
 text(",\"static_ram_bytes\":");number((uintptr_t)&_bss_end-0x20000000u);
 text(guard?",\"stack_guard\":true":",\"stack_guard\":false");
}
'''
assert 'static void stack_paint' not in s;s=functions+s
s=s.replace('number(reject_count);text("}\\n");return 1;', 'number(reject_count);stack_report();text("}\\n");return 1;');assert 'stack_report();' in s;p.write_text(s)
p=r/'scripts/build_cc2538_fast.py';s=p.read_text().replace("'hardware/renode_cc2538/link.ld'", "'hardware/cc2538_q22/link_stack.ld'")
s=s.replace("'mode_attention=1;last_pid", "'stack_paint();mode_attention=1;last_pid")
p.write_text(s)
p=r/'scripts/audit_cc2538_fast.py';s=p.read_text().replace("image=r/'outputs/cc2538_fast/firmware.elf'", "image=(out/'firmware.elf') if (out/'firmware.elf').exists() else r/'outputs/cc2538_fast/firmware.elf'")
anchor=" report.update(status='passed'"
extra=" statuses=[v for rs in all_records for v in rs if v['event']=='local_status']\n if any('observed_stack_bytes' in v for v in statuses):\n  assert len(statuses)==4 and all(v['stack_guard'] and v['observed_stack_bytes']+v['static_ram_bytes']<32768 for v in statuses)\n  report.update(observed_stack_bytes=[v['observed_stack_bytes'] for v in statuses],static_ram_bytes=[v['static_ram_bytes'] for v in statuses],stack_guard_intact=True,stack_scope='Observed tested paths, not a worst-case stack bound')\n"
assert anchor in s;s=s.replace(anchor,extra+anchor);p.write_text(s)

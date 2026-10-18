"""Keep signed and source-only MAC endpoints separate in every summary."""
from pathlib import Path
import json,collections,hashlib
from audit_cc2538_v2 import audit_run as baseline_audit
from audit_cc2538_q22 import audit_run as quant_audit
from audit_cc2538_fast import audit_run as fast_audit
r=Path(__file__).resolve().parents[1];rows=[];timing={};private=[]
for profile,audit in [('cc2538_v2',baseline_audit),('cc2538_q22',quant_audit),('cc2538_fast',fast_audit)]:
 for topology in ['chain','choice']:
  out=r/'outputs'/profile/f'{topology}_100';d=audit(out,100,topology);(out/'audit.json').write_text(json.dumps(d,indent=2)+'\n')
  samples=d['emulated_receipt_delays'];fast=d.get('fast_source_receipt_delays',[])
  row=dict(profile=profile,topology=topology,offered=100,delivered=d['unique_sink_deliveries'],ed25519_receipts=d['unique_source_verified_receipts'],signed_delay_ms=[min(x['receipt_delay_ms'] for x in samples),max(x['receipt_delay_ms'] for x in samples)],signed_deadline_misses=sum(x['receipt_delay_ms']>[90,350,1500][x['traffic']] for x in samples),decisions=d['mcu_policy_decisions'],max_logit_error=d['max_logit_error'],max_feature_error=d['max_feature_error'],controls=d['rejection_controls'])
  if fast:row.update(fast_delay_ms=[min(x['receipt_delay_ms'] for x in fast),max(x['receipt_delay_ms'] for x in fast)],fast_deadline_misses=sum(x['receipt_delay_ms']>[90,350,1500][x['traffic']] for x in fast),observed_stack_bytes=d['observed_stack_bytes'],static_ram_bytes=d['static_ram_bytes'],stack_guard_intact=d['stack_guard_intact'])
  rows.append(row);times=collections.defaultdict(list)
  for p in out.glob('uart_*.jsonl'):
   rs=[json.loads(l) for l in p.read_text().splitlines() if l.startswith('{') and l.endswith('}')]
   if profile=='cc2538_fast':
    acked=set();receipts=set();credited=set();counts=collections.Counter()
    for v in rs:
     if v['event'] in ['local_mac_ok','local_receipt']:
      identity=(v['pid'],v['peer']);(acked if v['event']=='local_mac_ok' else receipts).add(identity)
      if identity in acked and identity in receipts and identity not in credited:counts[v['peer']]+=1;credited.add(identity)
     if v['event']=='local_decision':
      import struct
      state=struct.unpack('!44f',bytes.fromhex(v['cache_hex']))
      assert all(int(state[11*i+9])==counts[i] for i in range(4)),'Credit assigned before both MAC and Ed25519 proof'
   for v in rs:
    if v['event']=='stage_time':times[v['stage']].append(v['elapsed_ms'])
  timing[f'{profile}/{topology}']={k:dict(n=len(v),min_ms=min(v),mean_ms=sum(v)/len(v),max_ms=max(v)) for k,v in times.items()}
  secret=json.loads(Path(d['private_fixture_file']).read_text());private.extend(bytes.fromhex(v) for v in list(secret['keys'].values())+[secret['sink_seed']])
for profile in ['cc2538_profile','cc2538_q22','cc2538_fast']:
 for p in (r/'outputs'/profile).rglob('*'):
  if p.is_file():
   data=p.read_bytes()
   for key in private:assert key not in data and key.hex().encode() not in data,'Private material in '+str(p)
out=r/'outputs/cc2538_fast/receipt_profiles_summary.json';out.write_text(json.dumps(dict(status='passed_scoped_comparison',rows=rows,stage_times=timing,fast_credit_gate_checked=True,private_values_absent_from_checked_public_outputs=True,physical_validation=False,signed_receipt_deadline_compliance=False,fast_endpoint_scope='Observed source/sink MAC deadline only; not the original public-signature deadline and not physical timing',independent_statistical_replication=False),indent=2)+'\n');print(json.dumps(rows,indent=2))

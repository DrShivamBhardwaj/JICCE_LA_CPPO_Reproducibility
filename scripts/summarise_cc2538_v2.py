"""Summarise longer private-provisioning diagnostics and check public leak boundary."""
from pathlib import Path
import json,hashlib
from audit_cc2538_v2 import audit_run
r=Path(__file__).resolve().parents[1];root=r/'outputs/cc2538_v2';runs=[];sessions=[];private_values=[]
for topology in ['chain','choice']:
 out=root/f'{topology}_100';d=audit_run(out,100,topology);(out/'audit.json').write_text(json.dumps(d,indent=2)+'\n');delays=d['emulated_receipt_delays'];sessions+=d['sessions']
 secret=json.loads(Path(d['private_fixture_file']).read_text());private_values += [bytes.fromhex(x) for x in list(secret['keys'].values())+[secret['sink_seed']]]
 runs.append(dict(topology=topology,offered=100,delivered=d['unique_sink_deliveries'],verified_source_receipts=d['unique_source_verified_receipts'],decisions=d['mcu_policy_decisions'],multiple_choices=d['multiple_choice_decisions'],max_feature_error=d['max_feature_error'],max_logit_error=d['max_logit_error'],receipt_delay_ms=[min(x['receipt_delay_ms'] for x in delays),max(x['receipt_delay_ms'] for x in delays)],deadline_misses=sum(x['receipt_delay_ms']>[90,350,1500][x['traffic']] for x in delays),authenticated_wire_records=d['independently_authenticated_wire_records'],rejected_controls=d['rejection_controls']))
assert len(sessions)==len(set(sessions))==8
public_files=[p for p in root.rglob('*') if p.is_file()]+list((r/'hardware/cc2538_live').glob('*.h'))+[r/'scripts/build_cc2538_v2.py',r/'scripts/run_cc2538_v2.py']
for p in public_files:
 data=p.read_bytes()
 for secret in private_values:
  if secret in data or secret.hex().encode() in data:raise AssertionError('Private fixture material found in public artifact: '+str(p))
(root/'summary.json').write_text(json.dumps(dict(status='passed_scoped_diagnostics',runs=runs,boot_sessions_distinct_across_runs=True,private_keys_absent_from_checked_public_outputs=True,physical_validation=False,deadline_compliance=False,protected_mcu_storage_validated=False,statistical_superiority_claim=False),indent=2)+'\n');print(json.dumps(runs,indent=2))

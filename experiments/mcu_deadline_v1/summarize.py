"""Keep functional acceptance separate from original signed-deadline compliance."""
from pathlib import Path
import json,hashlib,os
R=Path(__file__).resolve().parents[2];O=R/'outputs/mcu_deadline_v1'
rows=[]
for topology in ['chain','choice']:
    folder=O/(topology+'_100');d=json.loads((folder/'verification.json').read_text())
    if d['status']!='passed' or d['unique_sink_deliveries']!=100 or d['unique_source_verified_receipts']!=100:raise ValueError('Incomplete MCU functional acceptance')
    delays=d['emulated_receipt_delays'];misses=sum(x['receipt_delay_ms']>[90,350,1500][x['traffic']] for x in delays)
    rows.append(dict(topology=topology,offered=100,delivered=d['unique_sink_deliveries'],signed_receipts=d['unique_source_verified_receipts'],signed_deadline_misses=misses,signed_delay_ms=[min(x['receipt_delay_ms'] for x in delays),max(x['receipt_delay_ms'] for x in delays)],mcu_decisions=d['mcu_policy_decisions'],max_logit_error=d['max_logit_error'],negative_controls=d['rejection_controls']))
# Runtime private fixture values must never enter public outputs/artifacts.
secrets=[]
for file in Path(os.environ['WSN_PRIVATE_ROOT']).glob('*.private.json'):
    d=json.loads(file.read_text());secrets.extend(bytes.fromhex(x) for x in list(d['keys'].values())+[d['sink_seed']])
for file in O.rglob('*'):
    if not file.is_file():continue
    raw=file.read_bytes()
    for secret in secrets:
        if secret in raw or secret.hex().encode() in raw:raise ValueError('Runtime secret in public output: '+str(file))
result=dict(status='completed_compiler_only_pilot',optimization='O3 without fast-math; same signature endpoint and deadlines',rows=rows,original_signed_deadline_complete=sum(x['signed_deadline_misses'] for x in rows)==0,physical_validation=False,production_security_validated=False,private_secret_scan_passed=True,interpretation='Sequential functional diagnostics, not independent performance replicates. Historical O2 comparison is descriptive; host/runtime/toolchain differences are retained.')
(O/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

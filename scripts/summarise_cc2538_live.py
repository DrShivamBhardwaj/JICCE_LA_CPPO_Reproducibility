"""Rebuild the two-topology summary from directly audited captures."""
from pathlib import Path
import json
from audit_cc2538_live import audit_run
r=Path(__file__).resolve().parents[1];root=r/'outputs/cc2538_live';summary=[]
for topology in ['chain','choice']:
 d=audit_run(root/topology,10,topology);delays=d['emulated_receipt_delays']
 summary.append(dict(topology=topology,packets=10,verified_receipts=d['unique_source_verified_receipts'],decisions=d['mcu_policy_decisions'],multiple_choice_decisions=d['multiple_choice_decisions'],max_feature_error=d['max_feature_error'],max_logit_error=d['max_logit_error'],received_local_tx_records=d['independently_authenticated_wire_records'],emulated_receipt_delay_ms=[min(x['receipt_delay_ms'] for x in delays),max(x['receipt_delay_ms'] for x in delays)],emulated_deadline_misses=sum(x['receipt_delay_ms']>[90,350,1500][x['traffic']] for x in delays),controls=d['rejection_controls']))
(root/'summary.json').write_text(json.dumps(dict(status='passed_pilot_acceptance',runs=summary,physical_validation=False,physical_energy_j=None,deadline_compliance=False,scope='Two small emulated integration runs, not independent statistical replicates or measured hardware'),indent=2)+'\n')
print(json.dumps(summary,indent=2))

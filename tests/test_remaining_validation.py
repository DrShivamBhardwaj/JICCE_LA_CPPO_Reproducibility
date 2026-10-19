import importlib.util,json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('remaining_validation',Path(__file__).resolve().parents[1]/'scripts/audit_remaining_validation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture_root(tmp_path):
    d=tmp_path/'outputs/cc2538_fast';d.mkdir(parents=True)
    rows=[dict(profile=p,topology=t,offered=100,delivered=100,ed25519_receipts=100,signed_deadline_misses=34,fast_deadline_misses=0) for p in ['cc2538_v2','cc2538_q22','cc2538_fast'] for t in ['chain','choice']]
    f=d/'receipt_profiles_summary.json';f.write_text(json.dumps(dict(rows=rows)))
    return f,rows

def test_fast_private_success_cannot_pass_signed_endpoint(tmp_path):
    _,rows=fixture_root(tmp_path)
    result=m.assess(tmp_path)
    assert result['profiles']['cc2538_fast']['fast_private_deadline_misses']==0
    assert not result['checks'][0]['complete']
    assert result['status']=='incomplete'

def test_missing_topology_rejected(tmp_path):
    f,rows=fixture_root(tmp_path);f.write_text(json.dumps(dict(rows=rows[:-1])))
    with pytest.raises(ValueError,match='topology'):m.assess(tmp_path)

def test_partial_delivery_rejected(tmp_path):
    f,rows=fixture_root(tmp_path);rows[-1]['delivered']=99;f.write_text(json.dumps(dict(rows=rows)))
    with pytest.raises(ValueError,match='acceptance'):m.assess(tmp_path)

def test_lto_pass_flag_cannot_override_observed_packet_deadline(tmp_path):
    fixture_root(tmp_path)
    folder=tmp_path/'outputs/mcu_deadline_v2';folder.mkdir()
    rows=[dict(topology=t,offered=100,delivered=100,signed_receipts=100,signed_deadline_misses=0) for t in ['chain','choice']]
    (folder/'analysis.json').write_text(json.dumps(dict(status='completed_compiler_only_pilot',rows=rows,original_signed_deadline_complete=True)))
    for t in ['chain','choice']:
        capture=folder/(t+'_100');capture.mkdir()
        # Synthetic unit fixture: every critical packet is actually late.
        packets=[dict(pid=i,traffic=0,receipt_delay_ms=100) for i in range(100)]
        (capture/'verification.json').write_text(json.dumps(dict(status='passed',unique_sink_deliveries=100,unique_source_verified_receipts=100,emulated_receipt_delays=packets)))
    with pytest.raises(ValueError,match='deadline summary mismatch'):m.assess(tmp_path)

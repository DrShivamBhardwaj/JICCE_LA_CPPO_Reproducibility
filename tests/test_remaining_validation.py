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

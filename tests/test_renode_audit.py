"""Reject compromised/incomplete captures, without rerunning an emulator."""
import importlib.util,json,shutil,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mcu_audit',ROOT/'scripts/audit_renode_boards.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

@pytest.fixture
def capture(tmp_path):
    dest=tmp_path/'run';shutil.copytree(ROOT/'outputs/renode_boards/attention_strict_20261016',dest);return dest

def rewrite(path,fn):
    rows=[json.loads(x) for x in path.read_text().splitlines()];rows=fn(rows);path.write_text(''.join(json.dumps(x)+'\n' for x in rows))

def test_archived_complete_capture_passes(capture):
    assert audit.audit_run(capture,10)['source_verified_receipts']==10

def test_partial_sink_delivery_rejected(capture):
    p=capture/'verification.json';r=json.loads(p.read_text());r['sink_delivered']=9;p.write_text(json.dumps(r))
    with pytest.raises(audit.AuditError):audit.audit_run(capture,10)

def test_missing_source_receipt_rejected(capture):
    def drop(rows):
        def receipt(r):
            return r['event']=='board' and r['record']['event']=='rx' and bytes.fromhex(r['record']['wire'])[1]==3
        first=next(i for i,r in enumerate(rows) if receipt(r));return rows[:first]+rows[first+1:]
    rewrite(capture/'node_0.jsonl',drop)
    with pytest.raises(audit.AuditError,match='receipts incomplete'):audit.audit_run(capture,10)

def test_missing_final_rejected(capture):
    rewrite(capture/'node_1.jsonl',lambda rows:[r for r in rows if r['event']!='final'])
    with pytest.raises(audit.AuditError,match='final record'):audit.audit_run(capture,10)

def test_bad_negative_probe_rejected(capture):
    p=capture/'probes.json';r=json.loads(p.read_text());r[2]['ack']['ok']=True;p.write_text(json.dumps(r))
    with pytest.raises(audit.AuditError,match='Negative probe'):audit.audit_run(capture,10)

def test_future_only_transmission_rejected(capture):
    rewrite(capture/'node_0.jsonl',lambda rows:[dict(r,host_monotonic_s=1e30) if r['event']=='tx' else r for r in rows])
    with pytest.raises(audit.AuditError,match='prior matching'):audit.audit_run(capture,10)

def test_false_runtime_receipt_count_rejected(capture):
    rewrite(capture/'node_0.jsonl',lambda rows:[dict(r,accepted_source_receipts=9) if r['event']=='final' else r for r in rows])
    with pytest.raises(audit.AuditError,match='Runtime source'):audit.audit_run(capture,10)

def test_tampered_signature_rejected(capture):
    def tamper(rows):
        for r in rows:
            if r['event']=='board' and r['record']['event']=='rx' and bytes.fromhex(r['record']['wire'])[1]==3:
                raw=bytearray.fromhex(r['record']['wire']);raw[-17]^=1;r['record']['wire']=raw.hex();break
        return rows
    rewrite(capture/'node_0.jsonl',tamper)
    with pytest.raises((audit.AuditError,ValueError)):audit.audit_run(capture,10)

def test_cli_new_path_failure_nonzero(capture):
    p=capture/'verification.json';r=json.loads(p.read_text());r['sink_delivered']=1;p.write_text(json.dumps(r))
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/audit_renode_boards.py'),'--run',str(capture),'--expected-packets','10'],capture_output=True,text=True)
    assert proc.returncode==1 and json.loads(proc.stdout)['status']=='failed'


def test_missing_runtime_receipt_counter_rejected(capture):
    def remove(rows):
        for r in rows:
            if r['event']=='final':r.pop('accepted_source_receipts',None)
        return rows
    rewrite(capture/'node_0.jsonl',remove)
    with pytest.raises(audit.AuditError,match='count missing'):audit.audit_run(capture,10)

from pathlib import Path
import importlib.util,json
import pytest
r=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('feedback_audit',r/'scripts/audit_cooja_feedback.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
log=r/'outputs/cooja_feedback/geometry_corrected/COOJA.testlog'

def changed(tmp_path,fn):
 (tmp_path/'COOJA.testlog').write_text(fn(log.read_text()));return tmp_path

def test_missing_source_offer_cannot_pass(tmp_path):
 with pytest.raises(AssertionError):m.audit_run(changed(tmp_path,lambda x:'\n'.join(l for l in x.splitlines() if not ('"event":"cooja_offer","pid":59,' in l))))

def test_ack_gate_replay_detects_false_credit(tmp_path):
 def alter(x):
  rows=x.splitlines()
  for i,line in enumerate(rows):
   if '"event":"feedback","op":"ack"' in line and '"ok":1' in line:
    rows[i]=line.replace('"ok":1','"ok":0');break
  return '\n'.join(rows)
 with pytest.raises(AssertionError):m.audit_run(changed(tmp_path,alter))

def test_corrupt_authenticated_wire_detected(tmp_path):
 def alter(x):
  rows=x.splitlines()
  for i,line in enumerate(rows):
   if '"event":"local_tx"' in line:
    prefix,msg=line.split(' {',1);v=json.loads('{'+msg);wire=v['wire'];v['wire']=wire[:-2]+('00' if wire[-2:]!='00' else '01');rows[i]=prefix+' '+json.dumps(v,separators=(',',':'));break
  return '\n'.join(rows)
 with pytest.raises(AssertionError):m.audit_run(changed(tmp_path,alter))

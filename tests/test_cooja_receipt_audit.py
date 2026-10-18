import importlib.util
from pathlib import Path
import pytest
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cooja_audit',root/'scripts/audit_cooja_receipt_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
log=root/'outputs/cooja_receipt_transport/frozen_9runs/rx1.0_seed91001/COOJA.testlog'

def altered(tmp_path,transform):
 (tmp_path/'COOJA.testlog').write_text(transform(log.read_text()));return tmp_path

def test_log_success_marker_cannot_hide_missing_packet(tmp_path):
 p=altered(tmp_path,lambda s:'\n'.join(x for x in s.splitlines() if not ('OFFER seq=100 ' in x)))
 with pytest.raises(AssertionError,match='offered'):m.audit_run(p,1.0)

def test_wire_tampering_rejected(tmp_path):
 def corrupt(s):
  lines=s.splitlines()
  for i,line in enumerate(lines):
   if ' hex=' in line:
    prefix,wire=line.split(' hex=');wire=wire[:40]+('00' if wire[40:42]!='00' else '01')+wire[42:];lines[i]=prefix+' hex='+wire;break
  return '\n'.join(lines)
 with pytest.raises(AssertionError):m.audit_run(altered(tmp_path,corrupt),1.0)

def test_zero_packet_pilot_rejected():
 with pytest.raises(AssertionError):m.audit_run(root/'outputs/cooja_receipt_transport/pilot',1.0)

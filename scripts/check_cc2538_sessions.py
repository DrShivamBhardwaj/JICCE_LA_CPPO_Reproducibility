"""Check host persistent boot allocation; no MCU flash persistence claim."""
from pathlib import Path
import tempfile,sys,json,concurrent.futures
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'hardware/cc2538_live'))
from session_allocator import allocate

def reserve(path):return allocate(path)
if __name__=='__main__':
 with tempfile.TemporaryDirectory() as td:
  path=str(Path(td)/'sessions.json')
  first=allocate(path);second=allocate(path);assert max(first)<min(second)
  with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:groups=list(pool.map(reserve,[path]*12))
  ids=[x for g in groups for x in g];assert len(ids)==len(set(ids))==48 and min(ids)>max(second)
  Path(path).write_text(json.dumps(dict(next=2**64-2)))
  try:allocate(path)
  except ValueError:pass
  else:raise AssertionError('Counter overflow accepted')
 out=r/'outputs/cc2538_v2/session_allocator_checks.json';out.write_text(json.dumps(dict(status='passed',sequential_restart_allocations_disjoint=True,concurrent_reservations=12,unique_concurrent_sessions=48,overflow_rejected=True,scope='Host file allocator only. MCU NVM persistence remains unvalidated.'),indent=2)+'\n');print(out)

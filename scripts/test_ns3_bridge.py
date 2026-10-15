"""Meaningful bridge controls: physical range, two-hop delivery and radio proof."""
import ctypes as C
from pathlib import Path
lib=C.CDLL(str(Path(__file__).resolve().parents[1]/'build/libwsn_ns3.so'))
lib.bridge_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double];lib.bridge_step.argtypes=[C.c_double]
class E(C.Structure):_fields_=[('time',C.c_double)]+[(k,C.c_int) for k in ['kind','node','peer','pid','ok']]
def poll():
 events=[];e=E()
 while lib.bridge_poll(C.byref(e)):events.append({k:getattr(e,k) for k,_ in E._fields_})
 return events
a=(C.c_double*6)(0,0,30,0,60,0);lib.bridge_init(3,a,80001,40.)
lib.bridge_send(0,2,1,-1);lib.bridge_step(.1);events=poll()
assert not any(e['kind']==1 for e in events)
assert any(e['kind']==3 and not e['ok'] for e in events)
lib.bridge_send(0,1,2,-1);lib.bridge_step(.1);events=poll();assert any(e['kind']==1 and e['node']==1 for e in events)
lib.bridge_send(1,2,2,0);lib.bridge_step(.1);events=poll()
assert any(e['kind']==1 and e['node']==2 for e in events)
assert any(e['kind']==2 and e['node']==0 and e['peer']==1 for e in events)
lib.bridge_destroy();print('PASS: direct out-of-range failure, two-hop delivery, reverse radio forwarding proof')

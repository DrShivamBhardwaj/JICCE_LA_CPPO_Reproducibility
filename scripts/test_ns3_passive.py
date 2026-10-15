"""A watchdog must receive an actual radio frame, including hidden-observer control."""
import ctypes as C
from pathlib import Path
l=C.CDLL(str(Path(__file__).resolve().parents[1]/'build/libwsn_ns3_passive.so'))
l.bridge_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double];l.bridge_options.argtypes=[C.c_int,C.c_double];l.bridge_step.argtypes=[C.c_double];l.bridge_telemetry.argtypes=[C.c_int,C.POINTER(C.c_double)]
class E(C.Structure):_fields_=[('time',C.c_double)]+[(x,C.c_int) for x in ['kind','node','peer','pid','ok']]
def poll():
 e=E();a=[]
 while l.bridge_poll(C.byref(e)):a.append({k:getattr(e,k) for k,_ in E._fields_})
 return a
xy=(C.c_double*8)(0,0,30,0,60,0,120,0);l.bridge_options(0,40.);l.bridge_init(4,xy,81001,40.)
l.bridge_send(0,1,1,-1);l.bridge_step(.1);assert any(e['kind']==1 and e['node']==1 for e in poll())
l.bridge_send(1,2,1,0);l.bridge_step(.1);es=poll()
assert any(e['kind']==1 and e['node']==2 for e in es)
assert any(e['kind']==7 and e['node']==0 and e['peer']==1 and e['pid']==1 for e in es)
assert not any(e['kind']==7 and e['node']==3 for e in es)
assert not any(e['kind']==2 for e in es)
for node in range(4):
 t=(C.c_double*9)();l.bridge_telemetry(node,t);assert t[4]==0
l.bridge_destroy();print('PASS: actual passive overhear, out-of-range observer silence, no proof frames')

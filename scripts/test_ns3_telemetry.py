"""Check physical telemetry, radio proof cost, and state-time energy identity."""
import ctypes as C
from pathlib import Path
import numpy as np
l=C.CDLL(str(Path(__file__).resolve().parents[1]/'build/libwsn_ns3_telemetry.so'))
l.bridge_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double];l.bridge_options.argtypes=[C.c_int,C.c_double];l.bridge_step.argtypes=[C.c_double];l.bridge_telemetry.argtypes=[C.c_int,C.POINTER(C.c_double)]
class E(C.Structure):_fields_=[('time',C.c_double)]+[(k,C.c_int) for k in ['kind','node','peer','pid','ok']]
def poll():
 es=[];e=E()
 while l.bridge_poll(C.byref(e)):es.append({k:getattr(e,k) for k,_ in E._fields_})
 return es
def run(proofs):
 xy=(C.c_double*6)(0,0,30,0,60,0);l.bridge_options(proofs,40.);l.bridge_init(3,xy,80002,40.)
 l.bridge_beacon(1,50);l.bridge_step(.05);assert any(e['kind']==5 and e['node']==0 for e in poll())
 l.bridge_send(0,2,0,-1);l.bridge_step(.1);assert not any(e['kind']==1 for e in poll())
 l.bridge_send(0,1,1,-1);l.bridge_step(.1);assert any(e['kind']==1 and e['node']==1 for e in poll())
 l.bridge_send(1,2,1,0);l.bridge_step(.1);es=poll();assert any(e['kind']==1 and e['node']==2 for e in es)
 assert any(e['kind']==2 and e['node']==0 for e in es)==bool(proofs)
 l.bridge_receipt(2,1,1);l.bridge_step(.1);assert any(e['kind']==6 and e['node']==1 for e in poll())
 result=[]
 for node in range(3):
  a=(C.c_double*9)();l.bridge_telemetry(node,a);a=np.array(a);assert np.isclose(a[0],3*(.0174*a[6]+.0188*a[7]+.000020*a[8]),atol=1e-12);assert np.isclose(sum(a[6:]),.45,atol=1e-9);result.append(a)
 l.bridge_destroy();return np.array(result)
a=run(1);b=run(0);assert a[:,2].sum()>b[:,2].sum();assert a[:,4].sum()==1 and b[:,4].sum()==0
print('PASS: range, radio beacons and receipts, proof on/off airtime, state-time energy identity')

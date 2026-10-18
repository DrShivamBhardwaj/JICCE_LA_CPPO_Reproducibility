import ctypes as C,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
class Event(C.Structure):
    _fields_=[("time",C.c_double)]+[(x,C.c_int) for x in ["kind","node","peer","pid","ok"]]
def library():
    l=C.CDLL(str(ROOT/"build/libwsn_ns3_powered.so"))
    l.bridge_init.argtypes=[C.c_int,C.POINTER(C.c_double),C.c_int,C.c_double]
    l.bridge_step.argtypes=[C.c_double]
    l.bridge_options.argtypes=[C.c_int,C.c_double]
    l.bridge_power_budget.argtypes=[C.c_int,C.c_double]
    l.bridge_power_status.argtypes=[C.c_int,C.POINTER(C.c_double)]
    l.bridge_telemetry.argtypes=[C.c_int,C.POINTER(C.c_double)]
    return l
def poll(l):
    e=Event();out=[]
    while l.bridge_poll(C.byref(e)):out.append({k:getattr(e,k) for k,_ in Event._fields_})
    return out

@pytest.mark.parametrize("budget",[0.,.0003,.005,.05])
def test_depletion_stops_radio_and_freezes_energy(budget):
    l=library();xy=(C.c_double*4)(0,0,20,0)
    l.bridge_options(0,40.);l.bridge_init(2,xy,87001,40.)
    l.bridge_power_budget(0,budget)
    for pid in range(30):
        l.bridge_send(0,1,pid,-1);l.bridge_step(.05)
    es=poll(l);status=(C.c_double*5)();a=(C.c_double*9)();b=(C.c_double*9)()
    l.bridge_power_status(0,status);l.bridge_telemetry(0,a)
    assert status[0]==0 and status[4]==0
    assert a[0]==pytest.approx(budget,abs=1e-9)
    assert status[3]>0
    assert not [e for e in es if e["node"]==1 and e["kind"]==1 and e["time"]>status[2]+1e-9]
    for pid in range(30,40):l.bridge_send(1,0,pid,-1);l.bridge_step(.02)
    assert not [e for e in poll(l) if e["node"]==0 and e["kind"] in [1,7]]
    l.bridge_step(1.);l.bridge_telemetry(0,b)
    assert list(a)==list(b)
    l.bridge_destroy()

def test_sleep_residence_and_wakeup_reception():
    l=library();l.bridge_awake.argtypes=[C.c_int,C.c_int]
    xy=(C.c_double*4)(0,0,20,0);l.bridge_options(0,40.);l.bridge_init(2,xy,87001,40.)
    l.bridge_step(.01)
    l.bridge_awake(0,0);l.bridge_awake(1,0);l.bridge_step(.1)
    a=(C.c_double*9)();l.bridge_telemetry(0,a)
    assert a[8]>.099
    before=a[0];l.bridge_step(.1);l.bridge_telemetry(0,a)
    assert a[0]-before==pytest.approx(.1*3*.000020,abs=1e-8)
    l.bridge_awake(0,1);l.bridge_awake(1,1);l.bridge_step(.001)
    l.bridge_send(0,1,123,-1);l.bridge_step(.02)
    assert any(e["kind"]==1 and e["node"]==1 and e["pid"]==123 for e in poll(l))
    l.bridge_destroy()

def test_sleep_request_waits_for_pending_transaction():
    l=library();l.bridge_awake.argtypes=[C.c_int,C.c_int]
    l.bridge_duty_status.argtypes=[C.c_int,C.POINTER(C.c_double)]
    xy=(C.c_double*4)(0,0,20,0);l.bridge_options(0,40.);l.bridge_init(2,xy,87002,40.)
    l.bridge_send(0,1,1,-1);l.bridge_awake(0,0);l.bridge_step(.1)
    status=(C.c_double*3)();l.bridge_duty_status(0,status)
    assert status[0]==0 and status[2]>0
    assert any(e["kind"]==1 and e["node"]==1 for e in poll(l))
    l.bridge_destroy()

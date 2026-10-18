import itertools,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import pytest
from test_distributed_auth import setup_nodes
from wsn_sim.clock_envelope import ClockEnvelope

def test_all_675_clock_combinations_accept_fresh_authenticated_beacons():
    envelope=ClockEnvelope.from_limits(.04,100.,300.)
    for so,ro,sd,rd,t in itertools.product([-.02,-.005,0.,.005,.02],[-.02,-.005,0.,.005,.02],[-50,0,50],[-50,0,50],[1.,60.,300.]):
        a,b=setup_nodes()[:2];b.clock_envelope=envelope
        _,wire=a.beacon(1,1.,0,so+t*(1+sd*1e-6))
        b.receive(wire,0,ro+(t+.001)*(1+rd*1e-6))
        assert 0 in b.cache,(so,ro,sd,rd,t)
        b.receive(wire,0,ro+(t+.002)*(1+rd*1e-6))
        assert b.rejects.get("replay")==1

def test_forgery_and_frames_beyond_extended_window_still_rejected():
    a,b=setup_nodes()[:2];b.clock_envelope=ClockEnvelope(.07)
    _,wire=a.beacon(1,1.,0,1.)
    bad=wire[:-1]+bytes([wire[-1]^1])
    b.receive(bad,0,1.01);assert b.rejects["tag"]==1
    b.receive(wire,0,1.9);assert b.rejects["stale beacon"]==1
    assert not b.cache

def test_envelope_expands_freshness_window_and_is_not_synchronization():
    e=ClockEnvelope(.07)
    assert e.accepts(1.,1.80,.75)
    assert not e.accepts(1.,1.83,.75)
    assert e.expired(1.,1.83,.75)

@pytest.mark.parametrize("bound",[float("nan"),float("inf"),-.1])
def test_invalid_bound(bound):
    with pytest.raises(ValueError):ClockEnvelope(bound)

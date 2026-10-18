import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pytest
from wsn_sim.bounded_feedback import BoundedFeedbackLedger

@pytest.mark.parametrize("q", [0., .001, .04, .099, .5, 1.])
def test_total_credit_is_independent_of_evidence_partition(q):
    split = BoundedFeedbackLedger(2)
    whole = BoundedFeedbackLedger(2)
    for ledger in (split, whole):
        assert ledger.register(0, 1, 1, 0., q)
        ledger.acknowledge(0, 1, 1, True, .01)
    split.evidence(0, 1, 1, "passive", .02)
    split.evidence(0, 1, 1, "receipt", .03)
    whole.evidence(0, 1, 1, "receipt", .03)
    assert split.risk[0].a[1] == pytest.approx(whole.risk[0].a[1])
    assert split.risk[0].a[1] - 1 == pytest.approx(max(.05, q))

def test_ack_gate_duplicates_and_terminal_failure():
    ledger = BoundedFeedbackLedger(2)
    ledger.register(0, 1, 1, 0., .04)
    ledger.evidence(0, 1, 1, "receipt", .001)
    assert ledger.risk[0].a[1] == 1
    ledger.acknowledge(0, 1, 1, False, .01)
    ledger.acknowledge(0, 1, 1, True, .02)
    ledger.evidence(0, 1, 1, "receipt", .03)
    assert ledger.risk[0].a[1] == 1
    assert ledger.risk[0].b[1] == 1

def test_late_credit_has_explicit_retention_horizon():
    ledger = BoundedFeedbackLedger(2, retention_s=2.)
    ledger.register(0, 1, 1, 0., .9)
    ledger.acknowledge(0, 1, 1, True, .01)
    ledger.expire(.2)
    ledger.evidence(0, 1, 1, "receipt", 1.)
    ledger.evidence(0, 1, 1, "receipt", 1.1)
    assert ledger.risk[0].a[1] == pytest.approx(1.9)
    ledger.expire(2.)
    assert not ledger.watches
    with pytest.raises(ValueError):
        ledger.register(0, 1, 1, 2., .9)
    ledger.evidence(0, 1, 1, "receipt", 2.1)
    assert ledger.risk[0].a[1] == pytest.approx(1.9)

def test_capacity_pressure_and_reclamation_do_not_reassign_identity():
    ledger = BoundedFeedbackLedger(2, capacity=2)
    assert ledger.register(0, 1, 1, 0., .9)
    assert ledger.register(0, 1, 2, 0., .9)
    assert not ledger.register(0, 1, 3, 0., .9)
    ledger.expire(2.)
    assert ledger.register(0, 1, 4, 2., .9)
    ledger.acknowledge(0, 1, 3, True, 2.)
    ledger.evidence(0, 1, 3, "receipt", 2.)
    assert ledger.risk[0].a[1] == 1
    assert ledger.capacity_rejections == 1

def test_long_stream_bounds_watches_history_and_pair_state():
    ledger = BoundedFeedbackLedger(2, capacity=32, history_capacity=16)
    for pid in range(10000):
        t = pid * .1
        assert ledger.register(0, 1, pid, t, .04)
        ledger.acknowledge(0, 1, pid, True, t)
        ledger.evidence(0, 1, pid, "receipt", t)
        assert len(ledger.watches) <= 21
        assert len(ledger.updates) <= 16
    assert len(ledger.highest_pid) == 1

def test_invalid_input_and_clock_regression():
    ledger = BoundedFeedbackLedger(2)
    for q in [float("nan"), float("inf"), -.1, 1.1]:
        with pytest.raises(ValueError):
            ledger.register(0, 1, 1, 0., q)
    ledger.register(0, 1, 1, 1., .9)
    with pytest.raises(ValueError):
        ledger.expire(.5)
    with pytest.raises(ValueError):
        ledger.evidence(0, 1, 1, "invented", 1.)

def test_reordered_new_identifiers_are_accepted_within_bounded_window():
    ledger=BoundedFeedbackLedger(2)
    assert ledger.register(0,1,10,0.,.9)
    assert ledger.register(0,1,8,.01,.9)
    with pytest.raises(ValueError):
        ledger.register(0,1,8,.02,.9)
    assert ledger.register(0,1,100,.03,.9)
    assert not ledger.register(0,1,9,.04,.9)
    assert ledger.old_identity_rejections==1
    assert ledger.identity_bits[(0,1)].bit_length()<=64

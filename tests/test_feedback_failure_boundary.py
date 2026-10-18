"""Estimator invariants underlying the interpretation, not new performance trials."""
import numpy as np
import pytest
from wsn_sim.censored_feedback import FeedbackLedger

@pytest.mark.parametrize('mode', ['censored', 'naive', 'active'])
def test_positive_history_then_acknowledged_silence(mode):
    ledger = FeedbackLedger(2, mode)
    evidence = 'proof' if mode == 'active' else 'receipt'
    ledger.register(0, 1, 0, 0., .9)
    ledger.acknowledge(0, 1, 0, True, .01)
    ledger.evidence(0, 1, 0, evidence, .02)
    ledger.expire(.2)
    risk = ledger.risk[0]
    before = (risk.a[1], risk.b[1], risk.risk[1], risk.risk_ucb[1])
    for pid in range(1, 6):
        start = float(pid)
        ledger.register(0, 1, pid, start, .9)
        ledger.acknowledge(0, 1, pid, True, start + .01)
        ledger.expire(start + .2)
    assert risk.a[1] == before[0]
    if mode == 'censored':
        np.testing.assert_array_equal([risk.a[1], risk.b[1], risk.risk[1], risk.risk_ucb[1]], before)
    else:
        assert risk.b[1] > before[1]
        assert risk.risk[1] > before[2]

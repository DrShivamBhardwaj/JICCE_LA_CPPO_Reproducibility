import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import numpy as np
from wsn_sim.censored_feedback import FeedbackLedger

def test_failed_first_link_and_missing_evidence_are_censored():
    x=FeedbackLedger(3,'censored');x.register(0,1,10,0,.9);x.acknowledge(0,1,10,False,.01);x.evidence(0,1,10,'passive',.02);x.expire(1.)
    assert x.risk[0].a[1]==x.risk[0].b[1]==1
    x.register(0,2,11,1,.9);x.acknowledge(0,2,11,True,1.01);assert x.expire(1.2)==[(0,2,11)]
    assert x.risk[0].b[2]==1 and x.censored==2

def test_duplicate_overhears_and_receipts_cannot_inflate_evidence():
    x=FeedbackLedger(3,'censored');x.register(0,1,1,0,.9)
    x.evidence(0,1,1,'passive',.01);assert x.risk[0].a[1]==1
    x.acknowledge(0,1,1,True,.02);assert np.isclose(x.risk[0].a[1],1.45)
    x.evidence(0,1,1,'passive',.03);x.evidence(0,1,1,'receipt',.04);x.evidence(0,1,1,'receipt',.05)
    assert np.isclose(x.risk[0].a[1],1.9) and x.risk[1].a[1]==1

def test_late_receipt_can_resolve_censoring_without_negative_penalty():
    x=FeedbackLedger(3,'censored');x.register(0,1,1,0,.9);x.acknowledge(0,1,1,True,.01);x.expire(.2);x.evidence(0,1,1,'receipt',.3)
    assert np.isclose(x.risk[0].a[1],1.9) and x.risk[0].b[1]==1

def test_naive_and_frozen_controls_have_declared_different_updates():
    for mode in ['naive','frozen']:
        x=FeedbackLedger(3,mode);x.register(0,1,1,0,.9);x.acknowledge(0,1,1,True,.01);x.expire(.2)
        assert np.isclose(x.risk[0].b[1],1.9 if mode=='naive' else 1.)

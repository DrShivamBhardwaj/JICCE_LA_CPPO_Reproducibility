import copy
from pathlib import Path
import numpy as np
import yaml
from wsn_sim.network import WSNNetwork
from wsn_sim.security import SecurityRiskEstimator

def test_radio_draws_do_not_change_traffic_or_dynamics():
    cfg = yaml.safe_load((Path(__file__).parents[1]/'configs/af_v3_final.yaml').read_text())
    cfg['validation'] = {'split_streams':True}
    a, b = WSNNetwork(copy.deepcopy(cfg)), WSNNetwork(copy.deepcopy(cfg))
    a.link_rng.random(1000)
    assert np.array_equal(a.traffic_rng.random(100), b.traffic_rng.random(100))
    a.update_dynamic_state(); b.update_dynamic_state()
    assert np.array_equal(a.queue, b.queue)
    assert np.array_equal(a.interference, b.interference)

def test_risk_disabled_removes_uncertainty_and_anomaly_pathways():
    r = SecurityRiskEstimator(5, enabled=False)
    r.observe_forward(2, False, .9)
    r.observe_rate(2, 1.)
    assert np.all(r.risk == 0)
    assert np.all(r.risk_ucb == 0)

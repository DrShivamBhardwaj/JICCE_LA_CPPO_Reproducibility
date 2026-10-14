from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.config import load_config
from wsn_sim.counterfactual import evaluate_counterfactual_event
from wsn_sim.env import PacketRoutingEnv
from wsn_sim.rl import LocalAttentionActorCritic


def _tiny_stage4g1_cfg():
    cfg = load_config(ROOT / "configs" / "stage4f_frozen.yaml")
    cfg["clustering"]["roa_population"] = 4
    cfg["clustering"]["roa_iterations"] = 2
    cfg["rl"]["dynamic_update_every_packets"] = 1
    cfg["counterfactual_capture"] = {"enabled": True}
    cfg["trigger"]["threshold"] = 0.0
    cfg["trigger"]["stress_threshold"] = 0.0
    cfg["trigger"]["persistence"] = 1
    cfg["trigger"]["stress_persistence"] = 1
    cfg["trigger"]["cooldown_rounds"] = 0
    return cfg


def test_stage4g1_captures_post_dynamic_pre_recluster_snapshot():
    cfg = _tiny_stage4g1_cfg()
    env = PacketRoutingEnv(cfg)
    initial_reclusters = env.recluster_count
    env.reset_packet()
    env.reset_packet()
    event = env.consume_counterfactual_event()
    assert event is not None
    assert event["event_id"] == 1
    assert event["snapshot"].recluster_count == initial_reclusters
    assert env.recluster_count == initial_reclusters + 1
    assert "qos_debt_slope" in event["state"]
    assert "security_risk_p90" in event["state"]


def test_stage4g1_counterfactual_branches_are_isolated_and_diagnose_actionability():
    cfg = _tiny_stage4g1_cfg()
    cfg["counterfactual_capture"]["enabled"] = False
    env = PacketRoutingEnv(cfg)
    env.qos.delay_debt[0] = 8.0
    env.qos.loss_debt[0] = 4.0
    snapshot = env.fork_for_counterfactual()
    original_chs = list(env.chs)
    original_energy = env.net.energy.copy()

    b = snapshot.fork_for_counterfactual()
    info = b.apply_counterfactual_recluster(conditioned=True, roa_seed=1234)
    assert info["conditioned"] is True
    assert list(env.chs) == original_chs
    assert np.allclose(env.net.energy, original_energy)

    model = LocalAttentionActorCritic(
        env.builder.context_dim,
        env.builder.CANDIDATE_DIM,
        env.builder.k,
        hidden=16,
        n_costs=env.n_costs,
    )
    row = evaluate_counterfactual_event(
        snapshot=snapshot,
        state={"event_id": 1, "trigger_score": 0.5},
        model=model,
        horizon_packets=2,
        roa_seed=9876,
        schedule_seed=5432,
    )
    assert row["horizon_packets"] == 2
    assert 0.0 <= row["branch_assignment_change_fraction"] <= 1.0
    assert "delta_class_0_delay_violation_rate_conditioned_minus_trigger" in row
    # Current routing observations do not consume CH/assignment state. Stage-4G1
    # records this explicitly instead of silently treating topology as causal.
    assert row["topology_actionable_to_router"] is False
    assert row["routing_observation_linf_delta"] == 0.0


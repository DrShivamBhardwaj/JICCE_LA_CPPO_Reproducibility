from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wsn_sim.af_v4 import SlackAwareObservationBuilder, SlackAwarePacketRoutingEnv, SlackMonotoneAttentionActorCritic
from wsn_sim.config import load_config
from wsn_sim.env import PacketRoutingEnv


def _cfg():
    return load_config(ROOT / "configs" / "af_v3_final.yaml")


def test_v3_builder_remains_unchanged():
    env = PacketRoutingEnv(_cfg())
    assert env.builder.CANDIDATE_DIM == 10
    assert env.clustering_enabled is False


def test_slack_builder_has_exact_two_extra_features():
    env = SlackAwarePacketRoutingEnv(_cfg())
    assert isinstance(env.builder, SlackAwareObservationBuilder)
    assert env.builder.CANDIDATE_DIM == 12
    assert env.builder.obs_dim == env.builder.context_dim + env.builder.k * 12


def test_slack_features_are_bounded_and_candidate_local():
    env = SlackAwarePacketRoutingEnv(_cfg())
    obs = env.reset_packet()
    rows = obs.flat_obs[env.builder.context_dim:].reshape(env.builder.k, env.builder.CANDIDATE_DIM)
    valid = np.flatnonzero(obs.base_mask)
    assert len(valid) > 0
    assert np.all((rows[valid, -2] >= 0.0) & (rows[valid, -2] <= 1.0))
    assert np.all((rows[valid, -1] >= 0.0) & (rows[valid, -1] <= 1.0))


def test_monotone_actor_initial_pressure_coefficient_is_half():
    env = SlackAwarePacketRoutingEnv(_cfg())
    b = env.builder
    model = SlackMonotoneAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k, hidden=32, n_costs=env.n_costs)
    assert abs(float(model.pressure_coefficient.detach()) - 0.5) < 1e-6


def test_slack_monotone_actor_is_candidate_permutation_equivariant():
    env = SlackAwarePacketRoutingEnv(_cfg())
    b = env.builder
    torch.manual_seed(1701)
    model = SlackMonotoneAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k, hidden=32, n_costs=env.n_costs).eval()
    x = torch.randn(4, b.obs_dim)
    # Pressure feature is normalized by construction in real observations.
    cand = x[:, b.context_dim:].reshape(4, b.k, b.CANDIDATE_DIM)
    cand[..., -1] = torch.sigmoid(cand[..., -1])
    x = torch.cat([x[:, :b.context_dim], cand.reshape(4, -1)], dim=1)
    mask = torch.ones((4, b.k), dtype=torch.bool)
    perm = torch.tensor([3, 0, 7, 2, 6, 1, 5, 4], dtype=torch.long)
    with torch.no_grad():
        logits, value, cvalue = model(x, mask)
        ctx = x[:, :b.context_dim]
        c = x[:, b.context_dim:].reshape(4, b.k, b.CANDIDATE_DIM)
        x2 = torch.cat([ctx, c[:, perm].reshape(4, -1)], dim=1)
        logits2, value2, cvalue2 = model(x2, mask[:, perm])
    assert torch.allclose(logits2, logits[:, perm], atol=1e-6, rtol=1e-6)
    assert torch.allclose(value2, value, atol=1e-6, rtol=1e-6)
    assert torch.allclose(cvalue2, cvalue, atol=1e-6, rtol=1e-6)


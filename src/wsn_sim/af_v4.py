from __future__ import annotations

import math
import numpy as np
import torch
from torch import nn

from .env import PacketRoutingEnv
from .observation import CrossLayerObservationBuilder
from .rl import LocalAttentionActorCritic


class SlackAwareObservationBuilder(CrossLayerObservationBuilder):
    """AF-v4 development-only builder with two residual-path latency features.

    This class is deliberately isolated from the AF-v3 primary builder so the
    historical AF-v3 implementation remains unchanged. It is valid only for the
    no-clustering AF-v4 development protocol.
    """

    SLACK_FEATURE_DIM = 2

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        if self.cluster_aware:
            raise ValueError("AF-v4 slack-aware development requires cluster_aware_routing=false")
        self.CANDIDATE_DIM = self.BASE_CANDIDATE_DIM + self.SLACK_FEATURE_DIM
        self.obs_dim = self.context_dim + self.k * self.CANDIDATE_DIM

    def _candidate_row(
        self,
        net,
        sec,
        current: int,
        target: int,
        elapsed_s: float,
        traffic_class: int,
        chs=None,
        assignment=None,
    ):
        row, pdr, delay, progress, topology_meta = super()._candidate_row(
            net,
            sec,
            current,
            target,
            elapsed_s,
            traffic_class,
            chs=chs,
            assignment=assignment,
        )
        is_sink = target < 0
        next_dist = 0.0 if is_sink else net.distance(target, None)
        est_hops_after = max(
            0,
            int(math.ceil(next_dist / max(0.75 * net.radio_range, 1e-6))),
        )
        est_hops_after_norm = float(
            np.clip(est_hops_after / max(self.max_hops, 1), 0.0, 1.0)
        )
        remaining_slack = max(float(self.deadlines[traffic_class]) - float(elapsed_s), 0.0)
        estimated_total_path_delay = float(delay) * float(est_hops_after + 1)
        denom = max(remaining_slack, float(delay), 1e-6)
        pressure = estimated_total_path_delay / denom
        pressure_norm = float(np.clip(pressure, 0.0, 2.0) / 2.0)
        extra = np.asarray([est_hops_after_norm, pressure_norm], dtype=np.float32)
        return np.concatenate([row, extra]).astype(np.float32), pdr, delay, progress, topology_meta


class SlackAwarePacketRoutingEnv(PacketRoutingEnv):
    """AF-v4 development environment with an otherwise unchanged AF-v3 loop."""

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        if self.clustering_enabled:
            raise ValueError("AF-v4 slack-aware development requires clustering.enabled=false")
        self.builder = SlackAwareObservationBuilder(cfg)
        self.last_obs = None


class SlackMonotoneAttentionActorCritic(LocalAttentionActorCritic):
    """Local attention plus a shared nonnegative penalty on path-delay pressure.

    Candidate permutation equivariance is preserved because the same learned
    scalar coefficient and the corresponding candidate-local pressure feature
    are applied independently to every slot.
    """

    def __init__(
        self,
        context_dim: int,
        candidate_dim: int,
        n_actions: int,
        hidden: int = 128,
        n_costs: int = 6,
        pressure_feature_index: int | None = None,
        initial_pressure_coeff: float = 0.5,
    ):
        super().__init__(context_dim, candidate_dim, n_actions, hidden=hidden, n_costs=n_costs)
        self.pressure_feature_index = int(candidate_dim - 1 if pressure_feature_index is None else pressure_feature_index)
        if not 0 <= self.pressure_feature_index < candidate_dim:
            raise ValueError("invalid pressure feature index")
        coeff = float(initial_pressure_coeff)
        if coeff <= 0:
            raise ValueError("initial pressure coefficient must be positive")
        raw = math.log(math.expm1(coeff))
        self.pressure_beta_raw = nn.Parameter(torch.tensor(raw, dtype=torch.float32))

    @property
    def pressure_coefficient(self) -> torch.Tensor:
        return torch.nn.functional.softplus(self.pressure_beta_raw)

    def forward(self, obs: torch.Tensor, mask: torch.Tensor | None = None):
        ctx, cand = self._split(obs)
        ch = self.ctx_encoder(ctx)
        eh = self.cand_encoder(cand)
        q = self.query(ch).unsqueeze(-2)
        k = self.key(eh)
        logits = (q * k).sum(dim=-1) / math.sqrt(k.shape[-1]) + self.actor_bias(eh).squeeze(-1)
        pressure = cand[..., self.pressure_feature_index]
        logits = logits - self.pressure_coefficient * pressure
        if mask is not None:
            logits = logits.masked_fill(~mask.bool(), -1e9)
            m = mask.float().unsqueeze(-1)
            pooled = (eh * m).sum(dim=-2) / m.sum(dim=-2).clamp_min(1.0)
        else:
            pooled = eh.mean(dim=-2)
        vh = self.critic(torch.cat([ch, pooled], dim=-1))
        return logits, self.value(vh).squeeze(-1), self.cost_values(vh)


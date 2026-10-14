from __future__ import annotations
import numpy as np
from .observation import CandidateObservation, CrossLayerObservationBuilder


def _rows(obs: CandidateObservation, builder: CrossLayerObservationBuilder) -> np.ndarray:
    start = builder.context_dim
    return obs.flat_obs[start:].reshape(builder.k, builder.CANDIDATE_DIM)


def select_baseline_action(obs: CandidateObservation, builder: CrossLayerObservationBuilder, policy: str) -> int:
    """Select an action from exactly the same candidate set seen by the learned policy.

    This is intentionally observation-only: baselines do not receive attack ground truth
    or privileged topology state. `etx` uses link reliability/progress; `energy_risk_etx`
    adds residual energy, queue and posterior risk-UCB. `unshielded_etx` uses the base
    loop/range mask and is used only as a shield ablation.
    """
    rows = _rows(obs, builder)
    if policy == "unshielded_etx":
        mask = obs.base_mask
    else:
        mask = obs.mask
    valid = np.flatnonzero(mask)
    if len(valid) == 0:
        return 0
    pdr = np.clip(rows[:, 2], 1e-3, 1.0)
    progress = rows[:, 5]
    if policy in {"etx", "unshielded_etx"}:
        # Lower ETX is preferred, but require geographic progress to avoid a
        # high-PDR neighbour that makes negligible sink progress.
        cost = 1.0 / pdr - 0.45 * progress
    elif policy == "energy_risk_etx":
        energy = rows[:, 1]
        queue = rows[:, 4]
        risk_ucb = rows[:, 7]
        retry = rows[:, 8]
        cost = 1.0 / pdr - 0.40 * progress + 0.30 * (1.0 - energy) + 0.35 * queue + 0.65 * risk_ucb + 0.20 * retry
    else:
        raise ValueError(f"unknown baseline policy: {policy}")
    cost = np.where(mask, cost, np.inf)
    return int(np.argmin(cost))


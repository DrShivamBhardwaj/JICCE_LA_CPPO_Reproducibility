from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical


class MaskedActorCritic(nn.Module):
    """Simple MLP policy retained as an ablation baseline."""

    def __init__(self, obs_dim: int, n_actions: int, hidden: int = 128, n_costs: int = 2):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(obs_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.actor = nn.Linear(hidden, n_actions)
        self.value = nn.Linear(hidden, 1)
        self.cost_values = nn.Linear(hidden, n_costs)

    def forward(self, obs: torch.Tensor, mask: torch.Tensor | None = None):
        h = self.encoder(obs)
        logits = self.actor(h)
        if mask is not None:
            logits = logits.masked_fill(~mask.bool(), -1e9)
        return logits, self.value(h).squeeze(-1), self.cost_values(h)

    def act(self, obs: torch.Tensor, mask: torch.Tensor, deterministic: bool = False):
        logits, value, cvalue = self(obs, mask)
        dist = Categorical(logits=logits)
        action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        return action, dist.log_prob(action), value, cvalue


class LocalAttentionActorCritic(nn.Module):
    """Permutation-equivariant local candidate policy for scalable WSN routing.

    The observation is a fixed-length serialization only for batching. Candidate
    slots are processed by a shared encoder and scored by context-to-candidate
    attention, so permuting candidate slots permutes policy logits rather than
    changing their semantic meaning. The critic uses a masked pooled local
    neighborhood representation. This avoids node-ID-specific parameters and
    supports transfer across network sizes.
    """

    def __init__(self, context_dim: int, candidate_dim: int, n_actions: int, hidden: int = 128, n_costs: int = 6):
        super().__init__()
        self.context_dim = int(context_dim)
        self.candidate_dim = int(candidate_dim)
        self.n_actions = int(n_actions)
        self.ctx_encoder = nn.Sequential(nn.Linear(context_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.cand_encoder = nn.Sequential(nn.Linear(candidate_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.query = nn.Linear(hidden, hidden, bias=False)
        self.key = nn.Linear(hidden, hidden, bias=False)
        self.actor_bias = nn.Sequential(nn.Linear(hidden, hidden // 2), nn.Tanh(), nn.Linear(hidden // 2, 1))
        self.critic = nn.Sequential(nn.Linear(2 * hidden, hidden), nn.Tanh())
        self.value = nn.Linear(hidden, 1)
        self.cost_values = nn.Linear(hidden, n_costs)

    def _split(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        ctx = obs[..., : self.context_dim]
        rem = obs[..., self.context_dim :]
        cand = rem.reshape(*obs.shape[:-1], self.n_actions, self.candidate_dim)
        return ctx, cand

    def forward(self, obs: torch.Tensor, mask: torch.Tensor | None = None):
        ctx, cand = self._split(obs)
        ch = self.ctx_encoder(ctx)
        eh = self.cand_encoder(cand)
        q = self.query(ch).unsqueeze(-2)
        k = self.key(eh)
        logits = (q * k).sum(dim=-1) / math.sqrt(k.shape[-1]) + self.actor_bias(eh).squeeze(-1)
        if mask is not None:
            logits = logits.masked_fill(~mask.bool(), -1e9)
            m = mask.float().unsqueeze(-1)
            pooled = (eh * m).sum(dim=-2) / m.sum(dim=-2).clamp_min(1.0)
        else:
            pooled = eh.mean(dim=-2)
        vh = self.critic(torch.cat([ch, pooled], dim=-1))
        return logits, self.value(vh).squeeze(-1), self.cost_values(vh)

    def act(self, obs: torch.Tensor, mask: torch.Tensor, deterministic: bool = False):
        logits, value, cvalue = self(obs, mask)
        dist = Categorical(logits=logits)
        action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        return action, dist.log_prob(action), value, cvalue


@dataclass
class LagrangeController:
    budgets: np.ndarray
    lr: float = 0.02
    max_lambda: float = 50.0

    def __post_init__(self):
        self.budgets = np.asarray(self.budgets, dtype=float)
        self.lambdas = np.zeros_like(self.budgets, dtype=float)

    def update(self, observed_costs: np.ndarray, active: np.ndarray | None = None) -> np.ndarray:
        observed = np.asarray(observed_costs, dtype=float)
        delta = observed - self.budgets
        if active is not None:
            delta = delta * np.asarray(active, dtype=float)
        self.lambdas = np.clip(self.lambdas + self.lr * delta, 0.0, self.max_lambda)
        return self.lambdas.copy()


class ConstrainedPPO:
    """Lagrangian PPO with reward and vector-valued cost critics."""

    def __init__(self, model: nn.Module, lr: float = 3e-4, clip: float = 0.2, entropy_coef: float = 0.01, value_coef: float = 0.5):
        self.model = model
        self.opt = torch.optim.Adam(model.parameters(), lr=lr)
        self.clip = clip
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef

    def update(self, obs, masks, actions, old_logp, reward_adv, returns, cost_adv, cost_returns, lambdas, epochs: int = 4):
        lambdas_t = torch.as_tensor(lambdas, dtype=torch.float32, device=obs.device)
        stats = {}
        for _ in range(epochs):
            logits, values, cvalues = self.model(obs, masks)
            dist = Categorical(logits=logits)
            logp = dist.log_prob(actions)
            ratio = torch.exp(logp - old_logp)
            weighted_adv = reward_adv - (cost_adv * lambdas_t).sum(dim=-1)
            s1 = ratio * weighted_adv
            s2 = torch.clamp(ratio, 1.0 - self.clip, 1.0 + self.clip) * weighted_adv
            policy_loss = -torch.min(s1, s2).mean() - self.entropy_coef * dist.entropy().mean()
            value_loss = 0.5 * (values - returns).pow(2).mean()
            cost_value_loss = 0.5 * (cvalues - cost_returns).pow(2).mean()
            loss = policy_loss + self.value_coef * value_loss + self.value_coef * cost_value_loss
            self.opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.opt.step()
            stats = {
                "loss": float(loss.detach()),
                "policy_loss": float(policy_loss.detach()),
                "value_loss": float(value_loss.detach()),
                "cost_value_loss": float(cost_value_loss.detach()),
                "entropy": float(dist.entropy().mean().detach()),
            }
        return stats


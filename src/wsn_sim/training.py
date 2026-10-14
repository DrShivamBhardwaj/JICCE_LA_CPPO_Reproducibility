from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import torch
from .env import PacketRoutingEnv
from .rl import LocalAttentionActorCritic, ConstrainedPPO, LagrangeController


@dataclass
class RolloutBatch:
    obs: torch.Tensor
    masks: torch.Tensor
    actions: torch.Tensor
    old_logp: torch.Tensor
    reward_adv: torch.Tensor
    returns: torch.Tensor
    cost_adv: torch.Tensor
    cost_returns: torch.Tensor


def _gae(rewards, values, dones, gamma: float, lam: float):
    n = len(rewards)
    adv = np.zeros(n, dtype=np.float32)
    gae = 0.0
    for t in range(n - 1, -1, -1):
        next_value = 0.0 if dones[t] or t == n - 1 else values[t + 1]
        nonterminal = 0.0 if dones[t] else 1.0
        delta = rewards[t] + gamma * next_value * nonterminal - values[t]
        gae = delta + gamma * lam * nonterminal * gae
        adv[t] = gae
    return adv, adv + np.asarray(values, dtype=np.float32)


def _cost_gae(costs, cvalues, dones, gamma: float, lam: float):
    costs = np.asarray(costs, dtype=np.float32)
    cvalues = np.asarray(cvalues, dtype=np.float32)
    n, n_costs = costs.shape
    adv = np.zeros_like(costs)
    gae = np.zeros(n_costs, dtype=np.float32)
    for t in range(n - 1, -1, -1):
        next_v = np.zeros(n_costs, dtype=np.float32) if dones[t] or t == n - 1 else cvalues[t + 1]
        nonterminal = 0.0 if dones[t] else 1.0
        delta = costs[t] + gamma * next_v * nonterminal - cvalues[t]
        gae = delta + gamma * lam * nonterminal * gae
        adv[t] = gae
    return adv, adv + cvalues


class CPPOTrainer:
    def __init__(self, cfg: dict, device: str = "cpu"):
        self.cfg = cfg
        self.device = torch.device(device)
        self.env = PacketRoutingEnv(cfg)
        b = self.env.builder
        hidden = int(cfg.get("rl", {}).get("hidden", 128))
        self.model = LocalAttentionActorCritic(b.context_dim, b.CANDIDATE_DIM, b.k, hidden=hidden, n_costs=self.env.n_costs).to(self.device)
        rcfg = cfg.get("rl", {})
        self.ppo = ConstrainedPPO(self.model, lr=float(rcfg.get("learning_rate", 3e-4)), clip=float(rcfg.get("ppo_clip", 0.2)), entropy_coef=float(rcfg.get("entropy_coef", 0.01)))
        budgets = np.empty(self.env.n_costs, dtype=float)
        budgets[0::2] = self.env.qos.delay_budgets
        budgets[1::2] = self.env.qos.loss_budgets
        self.lagrange = LagrangeController(budgets, lr=float(rcfg.get("lagrange_lr", 0.03)))
        self.gamma = float(rcfg.get("gamma", 0.99))
        self.gae_lambda = float(rcfg.get("gae_lambda", 0.95))

    def collect(self, episodes: int, deterministic: bool = False):
        obs_l, mask_l, act_l, logp_l, val_l, cval_l, rew_l, cost_l, done_l = [], [], [], [], [], [], [], [], []
        episode_info = []
        terminal_costs = []
        classes = []
        for _ in range(int(episodes)):
            obs = self.env.reset_packet()
            ep_reward = 0.0
            while True:
                ot = torch.as_tensor(obs.flat_obs, dtype=torch.float32, device=self.device).unsqueeze(0)
                mt = torch.as_tensor(obs.mask, dtype=torch.bool, device=self.device).unsqueeze(0)
                with torch.no_grad():
                    action, logp, value, cvalue = self.model.act(ot, mt, deterministic=deterministic)
                res = self.env.step(int(action.item()))
                obs_l.append(obs.flat_obs.copy())
                mask_l.append(obs.mask.copy())
                act_l.append(int(action.item()))
                logp_l.append(float(logp.item()))
                val_l.append(float(value.item()))
                cval_l.append(cvalue.squeeze(0).cpu().numpy().astype(np.float32))
                rew_l.append(float(res.reward))
                cost_l.append(res.costs.copy())
                done_l.append(bool(res.done))
                ep_reward += res.reward
                if res.done:
                    info = dict(res.info)
                    info["episode_reward"] = float(ep_reward)
                    info["recluster_count"] = self.env.recluster_count
                    info["max_qos_debt"] = self.env.qos.max_normalized_debt
                    episode_info.append(info)
                    terminal_costs.append(res.costs.copy())
                    classes.append(int(res.info["traffic_class"]))
                    break
                obs = res.observation
                assert obs is not None

        reward_adv, returns = _gae(rew_l, val_l, done_l, self.gamma, self.gae_lambda)
        cost_adv, cost_returns = _cost_gae(cost_l, cval_l, done_l, self.gamma, self.gae_lambda)
        if reward_adv.std() > 1e-6:
            reward_adv = (reward_adv - reward_adv.mean()) / (reward_adv.std() + 1e-8)
        batch = RolloutBatch(
            obs=torch.as_tensor(np.asarray(obs_l), dtype=torch.float32, device=self.device),
            masks=torch.as_tensor(np.asarray(mask_l), dtype=torch.bool, device=self.device),
            actions=torch.as_tensor(np.asarray(act_l), dtype=torch.long, device=self.device),
            old_logp=torch.as_tensor(np.asarray(logp_l), dtype=torch.float32, device=self.device),
            reward_adv=torch.as_tensor(reward_adv, dtype=torch.float32, device=self.device),
            returns=torch.as_tensor(returns, dtype=torch.float32, device=self.device),
            cost_adv=torch.as_tensor(cost_adv, dtype=torch.float32, device=self.device),
            cost_returns=torch.as_tensor(cost_returns, dtype=torch.float32, device=self.device),
        )
        terminal_costs = np.asarray(terminal_costs, dtype=float)
        classes = np.asarray(classes, dtype=int)
        observed = np.zeros(self.env.n_costs, dtype=float)
        active = np.zeros(self.env.n_costs, dtype=float)
        for c in range(self.env.qos.n_classes):
            idx = classes == c
            if idx.any():
                observed[2*c:2*c+2] = terminal_costs[idx][:, 2*c:2*c+2].mean(axis=0)
                active[2*c:2*c+2] = 1.0
        return batch, episode_info, observed, active

    def train(self, updates: int, episodes_per_update: int, ppo_epochs: int = 4):
        logs = []
        for u in range(int(updates)):
            batch, infos, observed, active = self.collect(episodes_per_update, deterministic=False)
            lambdas = self.lagrange.update(observed, active)
            stats = self.ppo.update(batch.obs, batch.masks, batch.actions, batch.old_logp, batch.reward_adv, batch.returns, batch.cost_adv, batch.cost_returns, lambdas, epochs=ppo_epochs)
            delivered = np.mean([float(i.get("delivered", False)) for i in infos]) if infos else 0.0
            delay_vals = [float(i.get("delay_s", np.nan)) for i in infos if i.get("delivered", False)]
            logs.append({
                "update": u,
                "episodes": len(infos),
                "delivery_rate": delivered,
                "mean_delivered_delay_ms": 1000.0 * float(np.nanmean(delay_vals)) if delay_vals else np.nan,
                "mean_episode_reward": float(np.mean([i["episode_reward"] for i in infos])) if infos else np.nan,
                "max_qos_debt": self.env.qos.max_normalized_debt,
                "recluster_count": self.env.recluster_count,
                **{f"lambda_{j}": float(x) for j, x in enumerate(lambdas)},
                **stats,
            })
        return logs


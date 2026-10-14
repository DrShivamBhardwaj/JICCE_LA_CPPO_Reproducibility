from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from wsn_sim.config import load_config
from wsn_sim.training import CPPOTrainer
from wsn_sim.rl import LocalAttentionActorCritic, MaskedActorCritic
import run_af_v3_e1_confirmatory as e1

FROZEN = [
    13001,13003,13007,13009,13033,13037,13043,13049,13063,13093,
    13099,13103,13109,13121,13127,13147,13151,13159,13163,13171,
    13177,13183,13187,13217,13219,13229,13241,13249,13259,13267,
]


def test_e1_seed_vault_exact_and_unique():
    assert e1.SEEDS == FROZEN
    assert len(e1.SEEDS) == 30
    assert len(set(e1.SEEDS)) == 30


def test_e1_primary_config_and_arm_only_policy_difference():
    cfg = load_config(ROOT / "configs" / "af_v3_final.yaml")
    e1.validate_primary_config(cfg)
    attn = e1.configure_policy(CPPOTrainer(cfg), e1.ATTN)
    mlp = e1.configure_policy(CPPOTrainer(cfg), e1.MLP)
    assert isinstance(attn.model, LocalAttentionActorCritic)
    assert isinstance(mlp.model, MaskedActorCritic)
    assert attn.env.builder.obs_dim == mlp.env.builder.obs_dim
    assert attn.env.builder.k == mlp.env.builder.k == 8
    assert attn.env.n_costs == mlp.env.n_costs == 6
    assert np.allclose(attn.lagrange.budgets, mlp.lagrange.budgets)
    assert attn.gamma == mlp.gamma
    assert attn.gae_lambda == mlp.gae_lambda
    assert attn.env.chs == mlp.env.chs == []
    assert np.all(attn.env.assignment == -1)
    assert np.all(mlp.env.assignment == -1)


def test_e1_e0_archive_and_protocol_exist():
    assert (ROOT / "results/af_v3_e0_qualification/e0_record.json").is_file()
    assert (ROOT / "experiments/AF_V3_E1_CONFIRMATORY_PROTOCOL.md").is_file()
    assert (ROOT / "configs/af_v1_primary.yaml").is_file()


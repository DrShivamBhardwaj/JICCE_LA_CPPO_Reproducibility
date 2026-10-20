"""Evidence-guard tests for prospective block statistics; no new outcomes fabricated."""
from pathlib import Path
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.heldout_geometry_v2.design import generate_cases
from experiments.heldout_geometry_v2.analyze import (
    factorial_effect, holm_adjust, paired_inference, load_verified_cases,
)


def test_factorial_main_effects_and_interaction_are_distinct():
    v = {"censored": 0.2, "censored_proof": 0.18,
         "negative": 0.5, "negative_proof": 0.46}
    out = factorial_effect(v)
    assert out["negative_main"] == pytest.approx(0.29)
    assert out["proof_main"] == pytest.approx(-0.03)
    assert out["interaction"] == pytest.approx(-0.02)


def test_holm_family_never_uses_packet_count_as_sample_size():
    family = [
        {"p_unadjusted": p, "geometry_blocks": 30}
        for p in (0.001, 0.02, 0.04, 0.07, 0.4, 0.9)
    ]
    holm_adjust(family)
    assert all(item["p_holm"] >= item["p_unadjusted"] for item in family)
    adj = [x["p_holm"] for x in sorted(family, key=lambda x: x["p_unadjusted"])]
    assert adj == sorted(adj)
    assert all(x["geometry_blocks"] == 30 for x in family)


def test_signflip_cluster_bootstrap_is_deterministic_for_constant_effect():
    x = [0.1] * 30
    a = paired_inference(x, np.random.default_rng(261021))
    b = paired_inference(x, np.random.default_rng(261021))
    assert a == b
    assert a["mean_difference"] == pytest.approx(0.1)
    assert a["ci95"] == pytest.approx([0.1, 0.1], abs=1e-12)
    assert a["p_unadjusted"] < 0.001


def test_incomplete_archive_is_never_mistaken_for_new_result():
    cases = [{**c, "case_id": f"never_collected_test_fixture_{i}"} for i, c in enumerate(generate_cases()[:2])]
    with pytest.raises(RuntimeError, match="INCOMPLETE"):
        load_verified_cases(cases)

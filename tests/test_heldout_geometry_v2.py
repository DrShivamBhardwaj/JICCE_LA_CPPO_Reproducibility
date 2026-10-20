"""Cheap, outcome-free acceptance tests for prospective independent-geometry validation."""
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "heldout_geometry_v2"))
from design import (
    ARMS, SINK, generate_blocks, generate_cases, geometry_quality,
    progress, validate_plan,
)


def test_frozen_plan_and_geometry_levels():
    path = ROOT / "experiments" / "heldout_geometry_v2" / "protocol.json"
    plan = json.loads(path.read_text())
    blocks, cases = validate_plan(plan)
    assert len(blocks) == 30
    assert len(cases) == 2880
    assert len({c["case_id"] for c in cases}) == 2880
    assert collections.Counter(b["geometry_stratum"] for b in blocks) == {
        "clipped": 15, "unclipped": 15
    }
    for category in ("clipped", "unclipped"):
        assert collections.Counter(
            b["permutation"] for b in blocks if b["geometry_stratum"] == category
        ) == {0: 8, 1: 7}
    assert all(b["checkpoint"] in (41001, 41002, 41003) for b in blocks)
    assert len({tuple(round(x, 6) for x in b["physical_positions"][0]) for b in blocks}) == 30


def test_two_hop_connectivity_and_progress_not_all_clipped():
    for block in generate_blocks():
        pos = block["physical_positions"]
        assert tuple(pos[3]) == SINK
        assert geometry_quality(pos, block["geometry_stratum"])
        assert math.dist(pos[0], pos[3]) > 50
        for relay in pos[1:3]:
            assert math.dist(pos[0], relay) < 48.5
            assert math.dist(pos[3], relay) < 48.5
        if block["geometry_stratum"] == "unclipped":
            assert all(progress(pos[0], p) < 0.985 for p in pos[1:3])
        else:
            assert all(progress(pos[0], p) > 1.035 for p in pos[1:3])


def test_full_within_geometry_factorial_without_oversampling_geometry():
    _, cases = generate_blocks(), generate_cases()
    assert all(c["case_id"].startswith("h2_") for c in cases)
    for block in range(30):
        rows = [c for c in cases if c["block"] == block]
        assert len(rows) == 96
        combinations = {
            (c["onset"], c["rx_probability"], c["timing"], c["physical_attacker"], c["arm"])
            for c in rows
        }
        assert len(combinations) == 96
        assert sum(c["physical_attacker"] == 0 for c in rows) == 32
        assert sum(c["physical_attacker"] != 0 for c in rows) == 64
        assert {c["checkpoint"] for c in rows} == {(41001, 41002, 41003)[block % 3]}
        for c in rows:
            assert c["proof"] == ARMS[c["arm"]][1]
            assert c["mode"] == ARMS[c["arm"]][0]
            if c["physical_attacker"] == 0:
                assert c["attacker"] == 0
            else:
                expected = c["physical_attacker"] if c["permutation"] == 0 else 3 - c["physical_attacker"]
                assert c["attacker"] == expected


def test_false_plan_mutations_are_rejected():
    import copy
    plan = json.loads(
        (ROOT / "experiments" / "heldout_geometry_v2" / "protocol.json").read_text()
    )
    for key, mutation in [
        ("blocks_sha256", "0" * 64),
        ("expected_runs", 100),
        ("design_seed", 3),
    ]:
        altered = copy.deepcopy(plan)
        altered[key] = mutation
        try:
            validate_plan(altered)
        except ValueError:
            pass
        else:
            raise AssertionError(f"bad plan accepted: {key}")


def test_original_scientific_evidence_still_frozen():
    prior = json.loads((ROOT / "outputs" / "remediation_v1" / "analysis.json").read_text())
    assert prior["runs"] == 1440
    assert prior["independent_geometry_blocks"] == 12
    primary = [
        x for x in prior["contrasts"]
        if x["endpoint"] == "post_delivery"
        and x["timing"] == 1
        and x["contrast"] == "negative_main"
    ]
    assert len(primary) == 1
    assert abs(primary[0]["mean_difference"] - 0.2117013888888889) < 1e-12

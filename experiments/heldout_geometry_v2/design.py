"""Prospective geometry-diverse validation design. No experimental outcomes in this module.

The sink remains fixed at (90, 0), as required by the frozen Cooja firmware.
Changing this coordinate without changing the actor feature code would be invalid.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
from pathlib import Path

SEED = 261020
BLOCKS = 30
CHECKPOINTS = (41001, 41002, 41003)
ONSETS = (10, 30)
RX_PROBABILITIES = (0.8, 1.0)
TIMINGS = (0, 1)
PHYSICAL_ATTACKERS = (0, 1, 2)
ARMS = {
    "censored": (0, 0),
    "censored_proof": (0, 1),
    "negative": (2, 0),
    "negative_proof": (2, 1),
}
SINK = (90.0, 0.0)
RADIO_RANGE = 50.0
LINK_MARGIN_RANGE = 48.5
PROGRESS_NORMALIZER = 38.0


def progress(source, relay):
    return (math.dist(source, SINK) - math.dist(relay, SINK)) / PROGRESS_NORMALIZER


def geometry_quality(positions, stratum):
    source, a, b, sink = positions
    if tuple(sink) != SINK or math.dist(source, sink) <= RADIO_RANGE:
        return False
    if min(math.dist(a, b), math.dist(source, sink)) < 12.0:
        return False
    for relay in (a, b):
        if math.dist(source, relay) >= LINK_MARGIN_RANGE:
            return False
        if math.dist(sink, relay) >= LINK_MARGIN_RANGE:
            return False
    p = [progress(source, a), progress(source, b)]
    if stratum == "unclipped":
        return all(0.52 < x < 0.985 for x in p)
    if stratum == "clipped":
        return all(x > 1.035 for x in p)
    raise ValueError("unknown geometry stratum")


def generate_blocks():
    rng = random.Random(SEED)
    blocks = []
    for block in range(BLOCKS):
        stratum = "clipped" if block % 2 == 0 else "unclipped"
        for attempt in range(10000):
            if stratum == "unclipped":
                source = [rng.uniform(10.5, 16.0), rng.uniform(-1.5, 1.5)]
                rx = (44.0, 49.0)
                ry = (10.5, 18.0)
            else:
                source = [rng.uniform(-1.0, 1.5), rng.uniform(-1.5, 1.5)]
                rx = (44.0, 46.5)
                ry = (10.5, 16.0)
            a = [rng.uniform(*rx), rng.uniform(*ry)]
            b = [rng.uniform(*rx), -rng.uniform(*ry)]
            positions = [source, a, b, list(SINK)]
            if geometry_quality(positions, stratum):
                break
        else:
            raise ValueError(f"no acceptable geometry for block {block}")
        blocks.append({
            "block": block,
            "geometry_stratum": stratum,
            "checkpoint": CHECKPOINTS[block % len(CHECKPOINTS)],
            "permutation": block % 2,
            "physical_positions": positions,
            "progress_unclipped": [progress(source, a), progress(source, b)],
            "link_distances_m": {
                "source_a": math.dist(source, a),
                "source_b": math.dist(source, b),
                "a_sink": math.dist(a, SINK),
                "b_sink": math.dist(b, SINK),
            },
        })
    return blocks


def generate_cases(blocks=None):
    if blocks is None:
        blocks = generate_blocks()
    cases = []
    for item in blocks:
        b = item["block"]
        permutation = item["permutation"]
        pos = item["physical_positions"]
        positions = [pos[0], pos[1 + permutation], pos[2 - permutation], pos[3]]
        for onset, rx, timing, physical_attacker, arm in itertools.product(
            ONSETS, RX_PROBABILITIES, TIMINGS, PHYSICAL_ATTACKERS, ARMS
        ):
            attacker = physical_attacker if permutation == 0 else (3 - physical_attacker if physical_attacker else 0)
            seed = SEED + 100 * b + 10 * ONSETS.index(onset) + RX_PROBABILITIES.index(rx)
            case_id = (
                f"h2_b{b:02d}_on{onset}_rx{int(rx * 100):03d}"
                f"_t{timing}_a{physical_attacker}_{arm}"
            )
            cases.append({
                "case_id": case_id,
                "block": b,
                "geometry_stratum": item["geometry_stratum"],
                "checkpoint": item["checkpoint"],
                "permutation": permutation,
                "onset": onset,
                "rx_probability": rx,
                "timing": timing,
                "physical_attacker": physical_attacker,
                "attacker": attacker,
                "arm": arm,
                "mode": ARMS[arm][0],
                "proof": ARMS[arm][1],
                "seed": seed,
                "positions": positions,
            })
    return cases


def validate_plan(plan):
    if plan["status"] != "prospective_unexecuted":
        raise ValueError("unexpected research classification")
    blocks = generate_blocks()
    cases = generate_cases(blocks)
    if len(cases) != 2880 or len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("incomplete or duplicate design")
    if len(blocks) != BLOCKS or sum(b["geometry_stratum"] == "unclipped" for b in blocks) != 15:
        raise ValueError("wrong independent geometry/stratum coverage")
    if plan["design_seed"] != SEED or plan["expected_runs"] != len(cases):
        raise ValueError("design/protocol mismatch")
    if plan["blocks"] != blocks:
        raise ValueError("frozen geometry differs from generator")
    if plan["factor_levels"] != {
        "onset": list(ONSETS), "rx_probability": list(RX_PROBABILITIES),
        "timing": list(TIMINGS), "physical_attacker": list(PHYSICAL_ATTACKERS),
        "arm": list(ARMS),
    }:
        raise ValueError("factorial levels differ from freeze")
    for b in blocks:
        subset = [c for c in cases if c["block"] == b["block"]]
        if len(subset) != 96 or set(c["arm"] for c in subset) != set(ARMS):
            raise ValueError("within-block factorial coverage")
    return blocks, cases


def validate_source_blobs(plan, root=None):
    import subprocess
    root = root or Path(__file__).resolve().parents[2]
    for path, expected in plan["base_git_blob_sha1"].items():
        output = subprocess.run(
            ["git", "-C", str(root), "hash-object", str(root / path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if output != expected:
            raise ValueError(f"Frozen dependency changed: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate committed plan and frozen dependencies")
    parser.add_argument("--export", type=Path, help="Write case manifest, with no outcomes")
    args = parser.parse_args()
    plan = json.loads((Path(__file__).parent / "protocol.json").read_text())
    blocks, cases = validate_plan(plan)
    if args.check:
        validate_source_blobs(plan)
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(json.dumps({"classification": "unexecuted_design", "cases": cases}, indent=2) + "\n")
    print(json.dumps({
        "status": "plan_validated_not_executed",
        "geometry_blocks": len(blocks),
        "clipped_blocks": sum(b["geometry_stratum"] == "clipped" for b in blocks),
        "unclipped_blocks": sum(b["geometry_stratum"] == "unclipped" for b in blocks),
        "cases": len(cases),
        "attacked_cases": sum(c["physical_attacker"] > 0 for c in cases),
        "benign_cases": sum(c["physical_attacker"] == 0 for c in cases),
        "design_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()

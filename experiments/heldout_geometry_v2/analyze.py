"""Analysis for a *completed* prospective 2x2 held-out geometry study.

Refuses to write results until all 2880 independently audited cases exist.
Historical results and their multiplicity families are never reanalysed here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from design import generate_cases, validate_plan, validate_source_blobs

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "remediation_v1"))
from trace_tools import read_events
OUTPUT = ROOT / "outputs" / "heldout_geometry_v2"
ARMS = ("censored", "censored_proof", "negative", "negative_proof")
ENDPOINTS = ("post_delivery", "critical_failure", "tx_seconds")
CONTRASTS = ("negative_main", "proof_main", "interaction")


def factorial_effect(v):
    c0, c1, n0, n1 = [v[k] for k in ARMS]
    return {
        "negative_main": ((n0 - c0) + (n1 - c1)) / 2.0,
        "proof_main": ((c1 - c0) + (n1 - n0)) / 2.0,
        "interaction": (n1 - n0) - (c1 - c0),
    }


def holm_adjust(family):
    ordered = sorted(family, key=lambda item: item["p_unadjusted"])
    prior = 0.0
    for i, row in enumerate(ordered):
        prior = max(prior, min(1.0, row["p_unadjusted"] * (len(ordered) - i)))
        row["p_holm"] = prior


def paired_inference(block_effects, rng):
    x = np.asarray(block_effects, np.float64)
    if x.shape != (30,) or not np.isfinite(x).all():
        raise ValueError("30 finite geometry differences are required")
    draws = 200000
    flips = rng.choice(np.array([-1.0, 1.0]), size=(draws, 30))
    sample_means = (flips * x).mean(axis=1)
    observed = float(x.mean())
    p = (1 + int(np.count_nonzero(np.abs(sample_means) >= abs(observed) - 1e-14))) / (draws + 1)
    boot_index = rng.integers(0, 30, size=(20000, 30))
    interval = np.quantile(x[boot_index].mean(axis=1), [0.025, 0.975])
    return dict(mean_difference=observed, ci95=interval.tolist(), p_unadjusted=p, block_effects=x.tolist())


def load_verified_cases(cases):
    rows = []
    missing = [c["case_id"] for c in cases if not (OUTPUT / "runs" / c["case_id"] / "audit.json").is_file()]
    if missing:
        raise RuntimeError(f"INCOMPLETE: {len(missing)} / {len(cases)} audited cases missing; first={missing[0]}")
    for case in cases:
        a = json.loads((OUTPUT / "runs" / case["case_id"] / "audit.json").read_text())
        if a.get("status") != "independent_audit_passed":
            raise ValueError(f"Unverified run: {case['case_id']}")
        if a.get("antecedent_provenance", {}).get("status") != "passed_antecedent_event_checks":
            raise ValueError(f"Antecedent audit failed: {case['case_id']}")
        if a.get("config") != {"mode": case["mode"], "proof": case["proof"], "attack": int(case["attacker"] != 0), "timing": case["timing"]}:
            raise ValueError(f"Case condition mismatch: {case['case_id']}")
        raw, events = read_events(OUTPUT / "runs" / case["case_id"])
        if hashlib.sha256(raw).hexdigest() != a.get("log_sha256"):
            raise ValueError(f"Capture hash mismatch: {case['case_id']}")
        choices_before_onset = [v for v in events if v["event"] == "local_decision" and v["_node"] == 0 and v["pid"] < case["onset"]]
        previously_attacker = (choices_before_onset[-1]["peer"] == case["attacker"]) if choices_before_onset and case["physical_attacker"] else None
        benign_negative_expiries = (sum(v["event"] == "feedback" and v["_node"] == 0 and v["op"] == "expire" and v["seen"] <= 0 for v in events) if case["physical_attacker"] == 0 and case["mode"] == 2 else None)
        m = a["metrics"]
        if m["offered"] != 60 or m["post_attack_offered"] != 60 - case["onset"]:
            raise ValueError(f"Packet opportunities mismatch: {case['case_id']}")
        rows.append({
            **case,
            "post_delivery": m["post_attack_delivered"] / m["post_attack_offered"],
            "critical_failure": m["critical_failure"],
            "tx_seconds": a["total_tx_state_s"],
            "post_attack_delivered": m["post_attack_delivered"],
            "post_attack_offered": m["post_attack_offered"],
            "previously_attacker": previously_attacker,
            "benign_negative_expiries": benign_negative_expiries,
            "avoidance_within_20": m["recovered_within_20_opportunities"],
            "avoidance_right_censored": m["sustained_safe_choice_start_offset"] is None,
        })
    return rows


def analyze(rows):
    rng = np.random.default_rng(261021)
    results = []
    for endpoint in ENDPOINTS:
        family = []
        for timing in (0, 1):
            effect_by_block = []
            for block in range(30):
                attacked = [r for r in rows if r["block"] == block and r["timing"] == timing and r["physical_attacker"] != 0]
                values = {
                    arm: float(np.mean([r[endpoint] for r in attacked if r["arm"] == arm]))
                    for arm in ARMS
                }
                if len(attacked) != 32 or any(sum(r["arm"] == arm for r in attacked) != 8 for arm in ARMS):
                    raise ValueError("attacked within-block factorial incomplete")
                effect_by_block.append(factorial_effect(values))
            for contrast in CONTRASTS:
                effects = [v[contrast] for v in effect_by_block]
                family.append({
                    "endpoint": endpoint, "timing": timing, "contrast": contrast,
                    "geometry_blocks": 30, **paired_inference(effects, rng)
                })
        holm_adjust(family)
        results.extend(family)
    benign = []
    for timing in (0, 1):
        for rx in (0.8, 1.0):
            for arm in ARMS:
                sample = [r for r in rows if r["physical_attacker"] == 0 and r["timing"] == timing and r["rx_probability"] == rx and r["arm"] == arm]
                if len(sample) != 60:
                    raise ValueError("benign control incomplete")
                benign.append({
                    "timing": timing, "rx_probability": rx, "arm": arm,
                    "cases": len(sample),
                    "mean_delivery": float(np.mean([r["post_delivery"] for r in sample])),
                    "mean_critical_failure": float(np.mean([r["critical_failure"] for r in sample])),
                    "mean_tx_seconds": float(np.mean([r["tx_seconds"] for r in sample])),
                    "mean_source_failure_increments": float(np.mean([r["benign_negative_expiries"] for r in sample])) if arm.startswith("negative") else None,
                })
    strata = []
    for category in ("clipped", "unclipped"):
        for timing in (0, 1):
            subset = [r for r in rows if r["geometry_stratum"] == category and r["physical_attacker"] != 0 and r["timing"] == timing]
            means = {arm: float(np.mean([r["post_delivery"] for r in subset if r["arm"] == arm])) for arm in ARMS}
            strata.append({"category": category, "timing": timing, "geometry_blocks": 15,
                           "arm_means": means, "descriptive_effects": factorial_effect(means)})
    exposure = []
    for timing in (0, 1):
        for arm in ARMS:
            attacked = [r for r in rows if r["timing"] == timing and r["arm"] == arm and r["physical_attacker"] > 0]
            previously = [r for r in attacked if r["previously_attacker"] is True]
            if not previously:
                raise ValueError("No attacker-exposed choices in complete study")
            exposure.append({"timing": timing, "arm": arm, "attacked_cases": len(attacked),
                             "previously_attacker_cases": len(previously),
                             "safe_three_choices_within_20": sum(r["avoidance_within_20"] for r in previously),
                             "right_censored_cases": sum(r["avoidance_right_censored"] for r in previously),
                             "scope": "Descriptive exposure-stratified avoidance, not authenticated end-to-end recovery"})
    return {"status": "analysed_only_after_full_audit", "new_runs": len(rows),
            "geometry_blocks": 30, "contrast_families": results,
            "benign_controls": benign, "clipping_strata_exploratory": strata,
            "exposure_stratified_avoidance": exposure,
            "primary_inference_scope": "Independent geometry block; conditional sign-symmetry Monte Carlo test, not randomized assignment",
            "limitations": "No real MCU timing, production security, calibrated RF, physical current or fully independent holdout choice.",
            "physical_validation": False}


def main():
    plan_path = Path(__file__).parent / "protocol.json"
    plan = json.loads(plan_path.read_text())
    _, cases = validate_plan(plan)
    validate_source_blobs(plan)
    rows = load_verified_cases(cases)
    answer = analyze(rows)
    answer["protocol_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "analysis.json").write_text(json.dumps(answer, indent=2) + "\n")
    print(json.dumps({"status": answer["status"], "new_runs": answer["new_runs"], "geometry_blocks": answer["geometry_blocks"]}, indent=2))


if __name__ == "__main__":
    main()

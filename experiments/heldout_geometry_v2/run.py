"""Isolated Cooja execution wrapper for the geometry-diverse prospective study.

Imports the frozen v1 simulator/auditor without modifying its files or outputs.
The --smoke option executes technical preflights only; --execute needs the full
frozen 2880-case archive and is deliberately not CI-autostarted.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import multiprocessing
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "experiments" / "remediation_v1"
BUILD = ROOT / "build" / "remediation_v1"
OUTPUT = ROOT / "outputs" / "heldout_geometry_v2"
sys.path.insert(0, str(ROOT))
from experiments.heldout_geometry_v2.design import generate_cases, validate_plan, validate_source_blobs
sys.path.insert(0, str(BASE))


def frozen_engine():
    spec = importlib.util.spec_from_file_location("heldout_frozen_remediation_engine", BASE / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.B = BUILD
    module.OUT = OUTPUT
    if module.OUT == ROOT / "outputs" / "remediation_v1":
        raise RuntimeError("refuse overwrite of historical experiment")
    return module


def validated_cases():
    plan = json.loads((HERE / "protocol.json").read_text())
    _, cases = validate_plan(plan)
    validate_source_blobs(plan)
    return cases


def execute_new(case, preflight=False):
    base = frozen_engine()
    return base.execute((case, preflight))


def prepare_weights(cases):
    engine = frozen_engine()
    BUILD.mkdir(parents=True, exist_ok=True)
    for checkpoint in sorted({c["checkpoint"] for c in cases}):
        engine.export(checkpoint, BUILD / f"weights_{checkpoint}.h")


def select_smoke(cases):
    requests = [
        (0, 0, 0, 10, 1.0, "censored"),
        (1, 1, 1, 30, 0.8, "negative"),
        (0, 2, 0, 10, 1.0, "negative_proof"),
    ]
    selected = []
    for block, attacker, timing, onset, rx, arm in requests:
        found = next(c for c in cases if c["block"] == block and
            c["physical_attacker"] == attacker and c["timing"] == timing and
            c["onset"] == onset and c["rx_probability"] == rx and c["arm"] == arm)
        selected.append({**found, "case_id": f"h2_technical_{len(selected)}"})
    return selected


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-only", action="store_true")
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    cases = validated_cases()
    print(json.dumps({"status": "design_verified", "declared_cases": len(cases),
                      "execution_requested": args.execute, "smoke_requested": args.smoke}), flush=True)
    if args.verify_only:
        return
    if not (BUILD / "cooja" / "build" / "libs" / "cooja.jar").exists():
        raise RuntimeError("Run bash experiments/remediation_v1/bootstrap.sh first")
    if args.smoke:
        selected = select_smoke(cases)
        prepare_weights(selected)
        for case in selected:
            report = execute_new(case, preflight=True)
            print(json.dumps(report), flush=True)
        (OUTPUT / "smoke_complete.json").write_text(json.dumps({
            "status": "three_technical_preflights_only",
            "number_of_scientific_experiment_runs": 0,
            "audited_preflight_cases": len(selected),
            "full_study_complete": False,
            "physical_validation": False,
        }, indent=2) + "\n")
        return
    prepare_weights(cases)
    preflight = [{**cases[i], "case_id": f"h2_preregistered_preflight_{i}"} for i in (0, 1)]
    for case in preflight:
        execute_new(case, preflight=True)
    if args.workers < 1 or args.workers > 8:
        raise ValueError("workers must be between 1 and 8")
    records = []
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        futures = [pool.submit(execute_new, c, False) for c in cases]
        for f in concurrent.futures.as_completed(futures):
            records.append(f.result())
            (OUTPUT / "progress.json").write_text(json.dumps({
                "status": "partial_until_all_cases", "completed": len(records),
                "expected": len(cases),
            }, indent=2) + "\n")
    if len(records) != len(cases):
        raise RuntimeError("Incomplete scientific study")
    (OUTPUT / "execution_complete.json").write_text(json.dumps({
        "status": "full_archive_ready_for_analysis",
        "cases": len(cases),
        "preflight_excluded": 2,
        "no_physical_validation": True,
    }, indent=2) + "\n")
    print("COMPLETE: audited cases", len(cases), flush=True)


if __name__ == "__main__":
    main()

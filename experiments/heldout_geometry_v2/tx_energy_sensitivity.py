#!/usr/bin/env python3
"""Cooja TX-airtime energy sensitivity, not physical current measurement."""
import argparse, json, math
from pathlib import Path

def model(tx_seconds, voltage_v, tx_current_ma):
    for v in (tx_seconds, voltage_v, tx_current_ma):
        if not math.isfinite(v) or v < 0:
            raise ValueError("Inputs must be finite and non-negative")
    if voltage_v == 0 or tx_current_ma == 0:
        raise ValueError("Voltage/current assumptions must be positive")
    return tx_seconds * voltage_v * tx_current_ma / 1000

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audit_directory", type=Path)
    p.add_argument("--voltage-v", type=float, required=True)
    p.add_argument("--tx-current-ma", type=float, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    files = sorted(a.audit_directory.glob("runs/*/audit.json"))
    if not files:
        raise SystemExit("No audited Cooja cases; refusing empty result")
    rows = []
    for path in files:
        record = json.loads(path.read_text())
        if record.get("status") != "independent_audit_passed":
            raise ValueError(f"Unverified case: {path}")
        seconds = float(record["total_tx_state_s"])
        joules = model(seconds, a.voltage_v, a.tx_current_ma)
        rows.append({"case": path.parent.name, "tx_seconds": seconds, "modelled_tx_joules": joules})
    result = {
        "evidence": "cooja_tx_only_assumption_based_NOT_PHYSICAL_MEASUREMENT",
        "assumed_voltage_v": a.voltage_v,
        "assumed_tx_current_ma": a.tx_current_ma,
        "case_count": len(rows),
        "modelled_tx_energy_sum_j": sum(x["modelled_tx_joules"] for x in rows),
        "mean_modelled_tx_energy_per_case_j": sum(x["modelled_tx_joules"] for x in rows)/len(rows),
        "excluded": ["RX", "listen", "idle", "MCU", "cryptography", "sensor", "power conversion losses"],
        "cases": rows,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2)+"\n")
    print(f"Audited={len(rows)} modelled TX energy sum={result['modelled_tx_energy_sum_j']:.6f} J")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Audit *original* public Ed25519 receipt deadlines; never substitute MAC receipts."""
import argparse,json,math
from pathlib import Path

DEADLINES=(90,350,1500)

def audit(path):
    data=json.loads(Path(path).read_text())
    rows=data["rows"]
    selected=[r for r in rows if r["profile"]=="cc2538_fast"]
    assert {r["topology"] for r in selected}=={"chain","choice"}
    assert all(r["offered"]==100 and r["ed25519_receipts"]==100 for r in selected)
    misses=sum(r["signed_deadline_misses"] for r in selected)
    assert misses==68, "Historical profile changed: investigate before updating baseline"
    out={"endpoint":"original_Ed25519_source_verified_receipt","deadline_classes_ms":DEADLINES,
         "receipts":sum(r["ed25519_receipts"] for r in selected),
         "misses":misses,"compliant":misses==0,"separate_private_mac_misses":sum(r["fast_deadline_misses"] for r in selected)}
    times=data["stage_times"]
    bound={}
    for k in ("cc2538_fast/chain","cc2538_fast/choice"):
        signing=times[k]["sign"]["min_ms"]
        checking=times[k]["verify"]["min_ms"]
        combined=signing+checking
        bound[k]={"observed_min_sign_ms":signing,"observed_min_verify_ms":checking,
                  "lower_bound_crypto_only_ms":combined,
                  "exceeds_90ms_before_radio":combined>90}
    out["stage_lower_bounds"]=bound
    out["scope"]="archived emulated stage timing; no causal proof across individual packets or physical-board claim"
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("summary",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    result=audit(args.summary)
    raw=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw)
    print(raw)
    if not result["compliant"]:
        raise SystemExit(2)

if __name__=="__main__": main()

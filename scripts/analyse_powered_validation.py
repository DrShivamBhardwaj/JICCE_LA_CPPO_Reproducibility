"""Reconcile exploratory powered/duty runs against retained final records."""
from pathlib import Path
import json,gzip,hashlib,statistics,itertools,sys
r=Path(__file__).resolve().parents[1];rows=[];traces=0;identities=0
for duty in [1.,.5,.2]:
 folder=r/"outputs/powered_feedback"/f"60s_87001_duty{duty}"
 run=json.loads((folder/"summary_87001_87003.json").read_text())
 assert {(x["seed"],x["arm"]) for x in run}==set(itertools.product(range(87001,87004),["censored_passive","bounded_passive","frozen_prior"]))
 assert len(run)==9
 for seed in range(87001,87004):
  with gzip.open(folder/f"trace_{seed}.jsonl.gz","rt") as f:finals=[json.loads(l) for l in f if '"type":"final"' in l]
  assert len(finals)==3;traces+=1
  for f in finals:
   x=next(x for x in run if (x["seed"],x["arm"])==(seed,f["arm"]))
   assert all(f[k]==v for k,v in x.items())
   for energy,pending,frames,bytecount,proofs,data,tx,rx,off in f["telemetry"]:
    assert abs(energy-3*(.0174*tx+.0188*rx+.000020*off))<1e-6
    identities+=1
 for x in run:
  assert x["post_cut_tx"]==0 and x["budget_overshoot_j"]<1e-8
  assert x["radio_energy_j"]<=50.+1e-6
  if x["arm"]=="bounded_passive":
   assert x["peak_watches"]<=128
 rows+=run
groups=[]
for duty,arm in itertools.product([1.,.5,.2],["censored_passive","bounded_passive","frozen_prior"]):
 xs=[x for x in rows if x["duty_fraction"]==duty and x["arm"]==arm]
 groups.append(dict(duty_fraction=duty,arm=arm,n=len(xs),delivery_percent=100*statistics.mean(x["delivery"] for x in xs),radio_energy_j=statistics.mean(x["radio_energy_j"] for x in xs),off_residence_s=statistics.mean(x["off_residence_s"] for x in xs),critical_violation_percent=100*statistics.mean(x["critical_violation"] for x in xs),final_watches=[x["ledger_final_watches"] for x in xs],depleted_sensors=[x["depleted_sensors"] for x in xs]))
result=dict(status="passed",runs=len(rows),trace_streams=traces,energy_identities=identities,groups=groups,scope="Exploratory paired ns-3.47 diagnostics, n=3; no confirmatory significance, equivalence or physical energy claim",sources={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/"src/ns3_bridge/powered_bridge.cc",r/"src/wsn_sim/bounded_feedback.py",r/"scripts/run_powered_feedback.py"]})
out=r/"outputs/validation_20261018/powered_analysis.json";out.write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))

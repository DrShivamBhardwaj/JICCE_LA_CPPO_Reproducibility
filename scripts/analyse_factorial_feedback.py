"""Analyze the separately frozen 30-fixture factorial extension."""
from pathlib import Path
import json,gzip,hashlib,itertools,math
import numpy as np
from scipy import stats
r=Path(__file__).resolve().parents[1];plan=json.loads((r/"configs/factorial_feedback_plan.json").read_text())
for p,h in plan["source_sha256"].items():assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h
rows=[];streams=0;identities=0
for duty in plan["duty"]:
 folder=r/"outputs/factorial_feedback"/f"4s_89001_duty{duty}"
 xs=json.loads((folder/"summary_89001_89030.json").read_text())
 assert len(xs)==120 and {(x["seed"],x["arm"]) for x in xs}==set(itertools.product(plan["fixtures"],plan["arms"]))
 for seed in plan["fixtures"]:
  with gzip.open(folder/f"trace_{seed}.jsonl.gz","rt") as h:finals=[json.loads(l) for l in h if '"type":"final"' in l]
  assert len(finals)==4;streams+=1
  for f in finals:
   x=next(x for x in xs if x["seed"]==seed and x["arm"]==f["arm"])
   assert all(f[k]==v for k,v in x.items())
   assert x["post_cut_tx"]==0 and x["budget_overshoot_j"]<1e-8 and x["peak_watches"]<=128
   if x["arm"].endswith("no_proof"):assert x["proof_requests"]==0
   for y in f["telemetry"]:
    assert abs(y[0]-3*(.0174*y[6]+.0188*y[7]+.000020*y[8]))<1e-6;identities+=1
 rows+=xs
contrasts=[]
def vector(duty,arm,metric):
 return np.array([next(x for x in rows if x["duty_fraction"]==duty and x["arm"]==arm and x["seed"]==seed)[metric] for seed in plan["fixtures"]],dtype=float)
def add(duty,kind,label,metric,diff):
 scale=100 if metric in ["delivery","critical_violation"] else 1
 diff=diff*scale;n=len(diff);mean=float(diff.mean());sd=float(diff.std(ddof=1));se=sd/math.sqrt(n);width=float(stats.t.ppf(.975,n-1))*se
 p=float(2*stats.t.sf(abs(mean/se),n-1)) if se>0 else (1. if mean==0 else 0.)
 contrasts.append(dict(duty_fraction=duty,kind=kind,label=label,endpoint=metric,n=n,mean_difference=mean,ci95=[mean-width,mean+width],p_unadjusted=p,units="percentage points" if scale==100 else "J"))
for duty,metric in itertools.product(plan["duty"],plan["endpoints"]):
 for mode in ["censored","naive"]:
  add(duty,"proof_traffic",mode,metric,vector(duty,mode+"_with_proof",metric)-vector(duty,mode+"_no_proof",metric))
 for proof in ["no_proof","with_proof"]:
  add(duty,"evidence_mode",proof,metric,vector(duty,"censored_"+proof,metric)-vector(duty,"naive_"+proof,metric))
 add(duty,"interaction","proof effect censored minus proof effect naive",metric,(vector(duty,"censored_with_proof",metric)-vector(duty,"censored_no_proof",metric))-(vector(duty,"naive_with_proof",metric)-vector(duty,"naive_no_proof",metric)))
assert len(contrasts)==30
highest=0.
for rank,i in enumerate(sorted(range(30),key=lambda i:contrasts[i]["p_unadjusted"])):
 highest=max(highest,min(1.,(30-rank)*contrasts[i]["p_unadjusted"]));contrasts[i]["p_holm"]=highest
means=[]
for duty,arm in itertools.product(plan["duty"],plan["arms"]):
 xs=[x for x in rows if x["duty_fraction"]==duty and x["arm"]==arm]
 means.append(dict(duty_fraction=duty,arm=arm,n=len(xs),delivery_percent=100*float(np.mean([x["delivery"] for x in xs])),critical_violation_percent=100*float(np.mean([x["critical_violation"] for x in xs])),radio_energy_j=float(np.mean([x["radio_energy_j"] for x in xs])),proof_requests=sum(x["proof_requests"] for x in xs),capacity_rejections=sum(x["ledger_capacity_rejections"] for x in xs)))
result=dict(status="passed",runs=len(rows),trace_streams=streams,energy_identities=identities,arm_means=means,contrasts=contrasts,holm_family=30,source_plan=plan,scope="Separate ns-3.47 factorial extension. Technical pilot and aborted 88001 captures excluded. Original confirmatory family unchanged; no equivalence claim.")
out=r/"outputs/validation_20261018/factorial_analysis.json";out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(dict(runs=len(rows),trace_streams=streams,energy_identities=identities,significant=[x for x in contrasts if x["p_holm"]<.05],arm_means=means),indent=2))

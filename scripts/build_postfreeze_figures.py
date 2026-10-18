"""Plot exact post-freeze factorial effects and the executed MCU boundary."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1];d=json.loads((r/"outputs/validation_20261018/factorial_analysis.json").read_text());out=r/"publication/array/postfreeze_figures";out.mkdir(exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"pdf.fonttype":42,"svg.fonttype":"none"})
xs=[x for x in d["contrasts"] if x["kind"]=="proof_traffic" and x["endpoint"]=="delivery"]
f,ax=plt.subplots(figsize=(7.1,3.4));colors=["#126e82","#ad6637","#126e82","#ad6637"]
for i,x in enumerate(xs):
 m=x["mean_difference"];lo,hi=x["ci95"];ax.errorbar(m,i,xerr=[[m-lo],[hi-m]],fmt="o",color=colors[i],capsize=4,lw=1.8)
 ax.text(4.8,i,f'Holm p={x["p_holm"]:.4g}',ha="right",va="center",fontsize=9)
ax.set_yticks(range(4),[("Always on" if x["duty_fraction"]==1 else "20% nominal")+" / "+x["label"] for x in xs]);ax.invert_yaxis();ax.axvline(0,color="#777",ls="--",lw=1);ax.set_xlim(-11,5)
ax.set_xlabel("Delivery difference with proof traffic minus without (percentage points)")
ax.grid(axis="x",color="#e0e0e0");ax.spines[["top","right"]].set_visible(False);f.tight_layout()
for ext in ["png","pdf","svg"]:f.savefig(out/f"fig11_factorial_delivery.{ext}",dpi=600,bbox_inches="tight")
plt.close(f)
(out/"provenance.json").write_text(json.dumps(dict(source="outputs/validation_20261018/factorial_analysis.json",contrast="with proof minus without proof",intervals="unadjusted paired Student t 95% intervals across 30 fixtures",p_values="Holm adjusted across 30 prespecified extension contrasts",no_smoothing=True),indent=2)+"\n")
print(out)

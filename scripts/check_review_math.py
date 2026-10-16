from pathlib import Path
import sys,json,hashlib,math
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from wsn_sim.rl import LocalAttentionActorCritic
from wsn_sim.security import SecurityRiskEstimator
from wsn_sim.censored_feedback import FeedbackLedger
from docx import Document
# Executable numerical identity, rather than source-string matching alone.
torch.manual_seed(73);model=LocalAttentionActorCritic(13,10,8,96,6).eval();x=torch.randn(4,93);mask=torch.ones(4,8,dtype=torch.bool);mask[0,5:]=False
with torch.no_grad():
 logits,_,_=model(x,mask);ctx,cand=model._split(x);q=model.query(model.ctx_encoder(ctx)).unsqueeze(-2);eh=model.cand_encoder(cand);k=model.key(eh)
 expected=((q*k).sum(-1)/math.sqrt(96)+model.actor_bias(eh).squeeze(-1)).masked_fill(~mask,-1e9)
 assert torch.equal(logits,expected)
 full=sum(p.numel() for p in model.parameters());actor=sum(p.numel() for name,p in model.named_parameters() if not name.startswith(('critic.','value.','cost_values.')))
# Retain and document the static-floor counterexample, never silently fix frozen results.
def credit(parts):
 risk=SecurityRiskEstimator(1)
 for part in parts:risk.observe_forward(0,True,.04*part)
 return float(risk.a[0]-1)
assert np.isclose(credit([.5,.5]),.1) and np.isclose(credit([1]),.05)
# XML has native fractions and summation characters, not flattened strings.
doc=Document(R/'publication/array/Array_Manuscript.docx');eq=doc._element.xpath('//m:oMath');assert len(eq)==10
from docx.oxml.ns import qn
checks={}
for i in [2,5,7,8,10]:
 assert eq[i-1].find('.//'+qn('m:f')) is not None;checks[str(i)]='native fraction present'
for i in [8,9]:
 text=''.join(eq[i-1].itertext());symbols=eq[i-1].xpath('.//m:chr/@m:val',namespaces={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'});assert '∑' in text or '∑' in symbols;checks[str(i)]='native summation present'
out=R/'outputs/review_math';out.mkdir(exist_ok=True)
result=dict(status='passed',attention_division_numeric_identity=True,model_parameters=full,actor_only_parameters=actor,full_fp32_bytes=4*full,actor_only_fp32_bytes=4*actor,static_floor_example={'q':.04,'two_half_credit':credit([.5,.5]),'one_full_credit':credit([1])},equation_structure=checks,source_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['src/wsn_sim/rl.py','src/wsn_sim/security.py']},embedded_memory_measured=False)
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

"""Audit the new matched ledger against independent Python and antecedent events."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
from trace_tools import read_events,causal_audit,run_metrics
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'src'))
from wsn_sim.censored_feedback import FeedbackLedger
spec=importlib.util.spec_from_file_location('archived_quantized_auditor',R/'scripts/audit_cooja_feedback_quantized.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class MatchedLedger(FeedbackLedger):
    def evidence(self,observer,peer,pid,kind,time):
        if self.mode!='naive':return super().evidence(observer,peer,pid,kind,time)
        key=(observer,peer,pid);w=self.watches.get(key)
        if w is None or kind=='proof' or (w.closed and w.acked is not True):return
        w.seen=max(w.seen,.5 if kind=='passive' else 1.);self._credit(key,w,time)

base.FeedbackLedger=MatchedLedger
_models={}
def audit_run(folder,case):
    key=case['checkpoint']
    if key not in _models:_models[key]=base.load_policy(R/f'outputs/jicce_validation/checkpoints/attention_{key}.pt','attention')
    base._MODEL=_models[key];base.XY=np.array(case['positions'],float)
    report=base.audit_run(folder)
    expected={'mode':case['mode'],'proof':case['proof'],'attack':int(case['attacker']!=0),'timing':case['timing']}
    if report['config']!=expected:raise ValueError('wrong runtime condition')
    raw,events=read_events(folder);report['antecedent_provenance']=causal_audit(events);report['metrics']=run_metrics(events,case['onset'],case['attacker']);report['checkpoint_sha256']=base.hashlib.sha256((R/f'outputs/jicce_validation/checkpoints/attention_{key}.pt').read_bytes()).hexdigest()
    return report

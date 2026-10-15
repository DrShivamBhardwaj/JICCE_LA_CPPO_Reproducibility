"""Receipt-assisted passive evidence with explicit censoring and deduplication.
Scores describe observed forwarding evidence; they are not IDS probabilities.
"""
from dataclasses import dataclass
from .security import SecurityRiskEstimator
@dataclass
class Watch:
    expected: float
    registered: float
    expiry: float | None = None
    acked: bool | None = None
    seen: float = 0.
    credited: float = 0.
    closed: bool = False
    timed_out: bool = False
class FeedbackLedger:
    def __init__(self,n_nodes,mode):
        if mode not in ['censored','naive','active','frozen']:raise ValueError(mode)
        self.mode=mode;self.risk=[SecurityRiskEstimator(n_nodes) for _ in range(n_nodes)]
        self.watches={};self.updates=[];self.censored=0;self.failures=0;self.positives=0
    def register(self,observer,peer,pid,time,expected):
        key=(observer,peer,pid)
        if key in self.watches:raise ValueError('duplicate registration')
        self.watches[key]=Watch(expected,time,time+.15 if self.mode=='active' else None)
    def _credit(self,key,w,time):
        if self.mode=='frozen' or w.acked is not True and self.mode!='active':return
        delta=w.seen-w.credited
        if delta<=0:return
        self.risk[key[0]].observe_forward(key[1],True,w.expected*delta)
        w.credited=w.seen;self.positives+=1
        self.updates.append(dict(time=time,key=list(key),success=True,weight=w.expected*delta))
    def acknowledge(self,observer,peer,pid,success,time):
        key=(observer,peer,pid);w=self.watches.get(key)
        if w is None:return
        w.acked=bool(success)
        if self.mode=='active':return
        if success:
            w.expiry=time+.15;self._credit(key,w,time)
        else:w.closed=True;self.censored+=1
    def evidence(self,observer,peer,pid,kind,time):
        key=(observer,peer,pid);w=self.watches.get(key)
        if w is None:return
        if self.mode=='active' and kind!='proof':return
        if self.mode!='active' and kind=='proof':return
        if w.closed and (self.mode!='censored' or w.acked is not True):return
        w.seen=max(w.seen,.5 if kind=='passive' else 1.)
        self._credit(key,w,time)
    def expire(self,time):
        expired=[]
        for key,w in self.watches.items():
            if w.closed or w.expiry is None or time<w.expiry:continue
            w.closed=True
            # A received passive transmission already supplies evidence. A
            # missing end-to-end receipt does not turn that into a failed hop.
            if w.seen>0:continue
            w.timed_out=True;expired.append(key)
            if self.mode in ['censored','frozen']:self.censored+=1
            else:
                self.risk[key[0]].observe_forward(key[1],False,w.expected);self.failures+=1
                self.updates.append(dict(time=time,key=list(key),success=False,weight=w.expected))
        return expired

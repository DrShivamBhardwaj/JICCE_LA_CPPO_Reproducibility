"""Local, delayed beacon observations for frozen-policy simulator transfer.
Feature slot 3 is received LQI rather than the training RSSI proxy.
"""
import numpy as np
from .observation import CandidateObservation
class TelemetryBuilder:
    k=8;CANDIDATE_DIM=10;context_dim=13;obs_dim=93
    def __init__(self,positions,deadlines):
        self.xy=np.asarray(positions);self.deadlines=np.asarray(deadlines);self.sink=len(positions)-1
    def build(self,node,traffic_class,elapsed,visited,now,own,cache,links,risk,qos):
        rows=np.zeros((8,10),np.float32);mask=np.zeros(8,bool);ids=np.full(8,-2,int)
        curdist=np.linalg.norm(self.xy[node]-self.xy[-1]);scored=[]
        for target,(energy,queue,timestamp,lqi) in cache.items():
            if target==node or target in visited or now-timestamp>.75 or energy<=0:continue
            d=np.linalg.norm(self.xy[node]-self.xy[target])
            if d>50:continue
            sink=target==self.sink;progress=curdist-np.linalg.norm(self.xy[target]-self.xy[-1]);a,b,delay=links.get(target,(9.,1.,.005));pdr=a/(a+b)
            row=np.array([sink,energy, pdr,lqi,queue,np.clip(progress/50,-1,1),0 if sink else risk.risk[target],0 if sink else risk.risk_ucb[target],min(1/pdr-1,4)/4,min(delay/self.deadlines[traffic_class],2)/2],np.float32)
            score=1.25*progress/50+.75*pdr+.25*row[1]-.55*row[7]-.2*queue
            scored.append((score,target,row))
        for slot,(_,target,row) in enumerate(sorted(scored,key=lambda x:(-x[0],x[1]))[:8]):rows[slot]=row;mask[slot]=True;ids[slot]=-1 if target==self.sink else target
        onehot=np.eye(3,dtype=np.float32)[traffic_class]
        ctx=np.r_[own[0],own[1],min(curdist/np.linalg.norm([150,150]),1),np.clip(1-elapsed/self.deadlines[traffic_class],0,1),onehot,qos.normalized_vector]
        return CandidateObservation(np.r_[ctx,rows.ravel()].astype(np.float32),mask,mask.copy(),ids,False)

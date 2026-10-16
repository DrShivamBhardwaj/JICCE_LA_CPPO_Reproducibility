"""Frozen-policy transfer using only authenticated cache and node-local state.

This is a new feature mapping, not the training observation distribution.
LQI replaces modeled RSSI; MAC outcomes estimate PDR; missing receipts are
censored. No network object, attack label or global position matrix is accepted.
"""
import math
from dataclasses import replace
import numpy as np
import torch
from .distributed_auth import Node, Pending, Datagram, HEADER, TAG
from .rl import LocalAttentionActorCritic, MaskedActorCritic

DEADLINES = np.array([.09, .35, 1.5])

def load_policy(path, arm):
    weights = torch.load(path, map_location='cpu', weights_only=True)
    costs = weights['cost_values.weight'].shape[0]
    if arm == 'attention':
        model = LocalAttentionActorCritic(13, 10, 8,
            hidden=weights['ctx_encoder.0.weight'].shape[0], n_costs=costs)
    elif arm == 'mlp':
        model = MaskedActorCritic(93, 8,
            hidden=weights['encoder.0.weight'].shape[0], n_costs=costs)
    else:
        raise ValueError(arm)
    model.load_state_dict(weights); model.eval()
    return model

def observation(state):
    """Pure reconstruction from explicit local inputs; all fields auditable."""
    own = state['own']; xy = state['xy']; sink_xy = state['sink_xy']
    now = state['now']; packet = state['packet']; traffic = packet['traffic']
    current = math.dist(xy, sink_xy); scored = []
    for raw_peer, cached in state['cache'].items():
        peer = int(raw_peer); x, y, energy, queue, stamp = cached
        if now-stamp > .75 or energy <= 0 or packet['visited'] & (1 << peer):
            continue
        progress = current-math.dist((x, y), sink_xy)
        if progress <= 0:
            continue
        a, b, delay = state['links'].get(str(peer), [9., 1., .005])
        pdr = a/(a+b); success = state['successes'].get(str(peer), 0)
        trust_a = 1.+success*pdr
        risk = .75/(trust_a+1.)
        ucb = min(1., risk+1.645*.75*math.sqrt(trust_a/((trust_a+1.)**2*(trust_a+2.))))
        is_sink = peer == state['sink']
        row = [float(is_sink), energy, pdr, state['lqi'].get(str(peer), 0.),
               queue, np.clip(progress/38., -1, 1), 0. if is_sink else risk,
               0. if is_sink else ucb, min(1./pdr-1., 4.)/4.,
               min(delay/DEADLINES[traffic], 2.)/2.]
        score = 1.25*progress/38.+.75*pdr+.25*energy-.55*row[7]-.2*queue
        scored.append((score, peer, row))
    ids = [-2]*8; rows = np.zeros((8,10), np.float32); mask = np.zeros(8,bool)
    for i, (_, peer, row) in enumerate(sorted(scored, key=lambda z:(-z[0],z[1]))[:8]):
        ids[i] = peer; rows[i] = row; mask[i] = True
    elapsed = max(0., now-packet['created_us']/1e6)
    debts = np.array(state['qos_debts']); debts = debts/(1.+debts)
    ctx = np.r_[own, min(current/math.hypot(150,150),1.),
                np.clip(1.-elapsed/DEADLINES[traffic],0.,1.),
                np.eye(3)[traffic], debts]
    return np.r_[ctx,rows.ravel()].astype(np.float32), mask, ids

class PolicyNode(Node):
    def __init__(self, *args, model=None, arm='greedy', audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.model=model; self.arm=arm; self.audit=audit
        self.own=(1.,0.); self.links={}; self.lqi={}; self.qos_debts=[0.]*6
        self.decisions=0; self.multichoice=0; self.source_deliveries=[]

    def snapshot(self, packet, now):
        return dict(node=self.id, xy=self.xy, sink=self.sink, sink_xy=self.sink_xy,
            own=self.own, now=now, cache=dict(self.cache), links=dict(self.links),
            lqi=dict(self.lqi), successes=dict(self.success_counts),
            qos_debts=list(self.qos_debts), packet=dict(traffic=packet.traffic,
            created_us=packet.created_us, visited=packet.visited, key=packet.key))

    def _forward(self, packet, previous, now):
        if packet.visited & (1<<self.id) or packet.hops >= 22:
            return []
        packet=replace(packet,visited=packet.visited|(1<<self.id),hops=packet.hops+1)
        state=self.snapshot(packet,now)
        # Canonicalize keys so saved JSON and runtime observation are identical.
        state['links']={str(k):v[:] for k,v in self.links.items()}
        state['lqi']={str(k):v for k,v in self.lqi.items()}
        state['successes']={str(k):v for k,v in self.success_counts.items()}
        obs,mask,ids=observation(state)
        if not mask.any():return []
        if self.arm=='greedy':
            peer=min((math.dist(self.cache[p][:2],self.sink_xy),self.cache[p][3],p)
                     for p in ids if p>=0)[2]
            probabilities=None
        else:
            with torch.no_grad():
                logits,_,_=self.model(torch.tensor(obs).unsqueeze(0),torch.tensor(mask).unsqueeze(0))
                probabilities=torch.softmax(logits,-1).squeeze(0).tolist()
            peer=ids[int(np.argmax(probabilities))]
        record=Pending(packet,previous,peer,now+2.)
        if not self._remember(record,now):return []
        self.decisions+=1; self.multichoice+=int(mask.sum()>1)
        if self.audit:self.audit(dict(event='decision',state=state,observation=obs.tolist(),
            mask=mask.tolist(),candidate_ids=ids,probabilities=probabilities,chosen=peer,arm=self.arm))
        return [(peer,self.channel.seal(2,peer,packet.encode()))]

    def ack(self,peer,wire,ok,now):
        super().ack(peer,wire,ok,now)
        if HEADER.unpack(wire[:HEADER.size])[1]!=2:return
        packet=Datagram.decode(wire[HEADER.size:-TAG]); record=self.pending.get(packet.key)
        if record is None or record.peer!=peer:return
        a,b,delay=self.links.get(peer,[9.,1.,.005])
        self.links[peer]=[a+int(ok),b+int(not ok),.8*delay+.2*max(0.,now-(record.expires-2.))]

    def receive_with_lqi(self,wire,peer,now,lqi):
        before=self.beacon_sequences.get(peer,-1)
        result=self.receive(wire,peer,now)
        if self.beacon_sequences.get(peer,-1)>before:self.lqi[peer]=float(np.clip(lqi/255.,0,1))
        return result

    def _settle(self,record,now,delivered):
        if record.settled:return
        c=record.packet.traffic; late=not delivered or now-record.packet.created_us/1e6>DEADLINES[c]
        self.qos_debts[2*c]=max(0.,self.qos_debts[2*c]+int(late)-[.015,.04,.1][c])
        self.qos_debts[2*c+1]=max(0.,self.qos_debts[2*c+1]+int(not delivered)-[.01,.03,.08][c])
        if self.id==record.packet.source and delivered:
            self.source_deliveries.append(dict(pid=record.packet.pid,traffic=c,receipt_delay_s=now-record.packet.created_us/1e6))
        super()._settle(record,now,delivered)

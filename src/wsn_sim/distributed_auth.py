"""Post-holdout reference transport. No shared route history or telemetry sidecar.
Pairwise HMAC-SHA256 authenticates hop messages. Ed25519 authenticates sink receipts.
Keys and expected boot sessions are provisioned out of band; no key exchange is claimed.
"""
from dataclasses import dataclass,replace
from collections import deque
import hashlib,hmac,math,struct
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
HEADER=struct.Struct('!BBHHQIH'); BEACON=struct.Struct('!fffHQ'); DATA=struct.Struct('!HIQBQB13sB'); RECEIPT=struct.Struct('!HIQ')
MAX_WIRE=114; MAX_NODES=104; TAG=16; DOMAIN=b'JICCE-hop-v1\0'; SOURCE=b'JICCE-source-v1\0'; SINK=b'JICCE-sink-v1\0'
class Rejected(ValueError):pass
@dataclass
class ReplayWindow:
    highest:int=-1
    bits:int=0
    def accept(self,seq):
        if seq>self.highest:
            gap=seq-self.highest
            self.bits=1 if self.highest<0 or gap>=64 else ((self.bits<<gap)|1)&((1<<64)-1)
            self.highest=seq;return True
        distance=self.highest-seq
        if distance>=64 or self.bits&(1<<distance):return False
        self.bits|=1<<distance;return True
class Channel:
    def __init__(self,node,session,keys,peer_sessions):
        self.node=node;self.session=session;self.keys=dict(keys);self.peer_sessions=dict(peer_sessions);self.seq=0;self.windows={}
        if not 0<=node<MAX_NODES or any(len(k)<32 for k in keys.values()):raise ValueError('node/key bounds')
    def seal(self,kind,peer,payload):
        if kind not in (1,2,3) or peer not in self.keys:raise Rejected('kind/peer')
        if self.seq>=2**32:raise Rejected('rotate session before sequence exhaustion')
        head=HEADER.pack(1,kind,self.node,peer,self.session,self.seq,len(payload));self.seq+=1;body=head+payload
        if len(body)+TAG>MAX_WIRE:raise Rejected('wire budget')
        return body+hmac.digest(self.keys[peer],DOMAIN+body,'sha256')[:TAG]
    def open(self,wire,mac_peer):
        if not HEADER.size+TAG<=len(wire)<=MAX_WIRE:raise Rejected('length')
        version,kind,sender,peer,session,seq,length=HEADER.unpack(wire[:HEADER.size])
        if version!=1 or kind not in (1,2,3) or peer!=self.node or sender!=mac_peer or sender not in self.keys:raise Rejected('envelope')
        if len(wire)!=HEADER.size+length+TAG:raise Rejected('length')
        tag=hmac.digest(self.keys[sender],DOMAIN+wire[:-TAG],'sha256')[:TAG]
        if not hmac.compare_digest(tag,wire[-TAG:]):raise Rejected('tag')
        if session!=self.peer_sessions[sender]:raise Rejected('unprovisioned session')
        if not self.windows.setdefault(sender,ReplayWindow()).accept(seq):raise Rejected('replay')
        return kind,sender,wire[HEADER.size:-TAG],seq
@dataclass(frozen=True)
class Datagram:
    source:int;pid:int;session:int;traffic:int;created_us:int;hops:int;visited:int;payload:bytes;source_tag:bytes
    @property
    def key(self):return self.source,self.pid,self.session
    def immutable(self):return struct.pack('!HIQBQB',self.source,self.pid,self.session,self.traffic,self.created_us,len(self.payload))+self.payload
    def encode(self):
        if not 0<=self.traffic<3 or not 0<=self.hops<=22 or self.visited>>MAX_NODES or len(self.payload)>24:raise Rejected('datagram bounds')
        return DATA.pack(self.source,self.pid,self.session,self.traffic,self.created_us,self.hops,self.visited.to_bytes(13,'big'),len(self.payload))+self.payload+self.source_tag
    @classmethod
    def decode(cls,payload):
        if len(payload)<DATA.size+TAG:raise Rejected('data length')
        src,pid,session,traffic,created,hops,visited,size=DATA.unpack(payload[:DATA.size])
        if len(payload)!=DATA.size+size+TAG or src>=MAX_NODES or traffic>=3 or hops>22:raise Rejected('data bounds')
        return cls(src,pid,session,traffic,created,hops,int.from_bytes(visited,'big'),payload[DATA.size:-TAG],payload[-TAG:])
@dataclass
class Pending:
    packet:Datagram;previous:int|None;peer:int|None;expires:float;acked:bool=False;receipt:bool=False;settled:bool=False;credited:bool=False
class Node:
    def __init__(self,node,xy,sink,sink_xy,channel,sink_public,sink_private=None,capacity=128,clock_envelope=None):
        self.clock_envelope=clock_envelope
        self.id=node;self.xy=tuple(xy);self.sink=sink;self.sink_xy=tuple(sink_xy);self.channel=channel;self.public=sink_public;self.private=sink_private;self.capacity=capacity
        self.cache={};self.beacon_sequences={};self.pending={};self.delivered={};self.delivered_total=0;self.accepted=deque(maxlen=capacity);self.success_counts={};self.debts=[0.,0.,0.];self.rejects={};self.settlements=0;self.evictions=0;self.max_pending=0;self.last_pid=-1
    def _fresh(self,stamp,now,ttl):
        if self.clock_envelope is None:
            return now-stamp<=ttl and stamp<=now+1e-6
        return self.clock_envelope.accepts(stamp,now,ttl)
    def _cache_expired(self,stamp,now):
        if self.clock_envelope is None:return now-stamp>.75
        return self.clock_envelope.expired(stamp,now,.75)
    def _remember(self,p,now):
        self.expire(now)
        if len(self.pending)>=self.capacity:self.evictions+=1;return False
        self.pending[p.packet.key]=p;self.max_pending=max(self.max_pending,len(self.pending));return True
    def beacon(self,peer,energy,queue,now):
        if not 0<=energy<=1 or not 0<=queue<=65535:raise Rejected('beacon bounds')
        return peer,self.channel.seal(1,peer,BEACON.pack(*self.xy,energy,queue,round(now*1e6)))
    def originate(self,pid,traffic,payload,now):
        if not isinstance(pid,int) or not self.last_pid<pid<2**32:raise Rejected('source packet counter')
        p=Datagram(self.id,pid,self.channel.session,traffic,round(now*1e6),0,0,bytes(payload),b'')
        if self.id==self.sink:raise Rejected('sink cannot originate test traffic')
        p=replace(p,source_tag=hmac.digest(self.channel.keys[self.sink],SOURCE+p.immutable(),'sha256')[:TAG]);p.encode();self.last_pid=pid;return self._forward(p,None,now)
    def _forward(self,packet,previous,now):
        if packet.visited&(1<<self.id) or packet.hops>=22:return []
        packet=replace(packet,visited=packet.visited|(1<<self.id),hops=packet.hops+1)
        current=math.dist(self.xy,self.sink_xy);choices=[]
        for peer,(x,y,energy,queue,stamp) in self.cache.items():
            if self._cache_expired(stamp,now) or energy<=0 or packet.visited&(1<<peer):continue
            distance=math.dist((x,y),self.sink_xy)
            if distance<current:choices.append((distance,queue,peer))
        if not choices:return []
        peer=min(choices)[2];encoded=packet.encode();record=Pending(packet,previous,peer,now+2.)
        if not self._remember(record,now):return []
        return [(peer,self.channel.seal(2,peer,encoded))]
    def _settle(self,r,now,delivered):
        if r.settled:return
        c=r.packet.traffic;late=not delivered or now-r.packet.created_us/1e6>[.09,.35,1.5][c]
        self.debts[c]=max(0.,self.debts[c]+int(late)-[.015,.04,.10][c]);r.settled=True;self.settlements+=1
    def ack(self,peer,wire,ok,now):
        try:
            kind=HEADER.unpack(wire[:HEADER.size])[1]
            if kind!=2:return
            p=Datagram.decode(wire[HEADER.size:-TAG]);r=self.pending.get(p.key)
            if r is None or r.peer!=peer:return
            r.acked=bool(ok)
            if r.receipt and r.acked and not r.credited:self.success_counts[peer]=self.success_counts.get(peer,0)+1;r.credited=True
        except (ValueError,struct.error):return
    def expire(self,now):
        for key,r in list(self.pending.items()):
            if now>=r.expires:self._settle(r,now,False);del self.pending[key]
        for identity,expiry in list(self.delivered.items()):
            if now>=expiry:del self.delivered[identity]
        # Cache contains only provisioned peers, with finite capacity by design.
        for peer,state in list(self.cache.items()):
            if self._cache_expired(state[-1],now):del self.cache[peer]
    def receive(self,wire,mac_peer,now):
        try:
            kind,peer,body,sequence=self.channel.open(wire,mac_peer)
            if kind==1:
                if len(body)!=BEACON.size:raise Rejected('beacon length')
                x,y,e,q,stamp_us=BEACON.unpack(body);stamp=stamp_us/1e6
                if not self._fresh(stamp,now,.75):raise Rejected('stale beacon')
                if sequence<=self.beacon_sequences.get(peer,-1):raise Rejected('older beacon')
                if not all(math.isfinite(v) for v in [x,y,e]) or not 0<=e<=1:raise Rejected('beacon values')
                self.beacon_sequences[peer]=sequence;self.cache[peer]=(x,y,e,q,stamp);self.accepted.append('beacon');return []
            if kind==2:
                packet=Datagram.decode(body)
                expected_session=self.channel.session if packet.source==self.id else self.channel.peer_sessions.get(packet.source)
                if packet.session!=expected_session:raise Rejected('source session')
                if not self._fresh(packet.created_us/1e6,now,2.) or packet.visited&(1<<self.id):raise Rejected('stale/loop data')
                if not packet.visited&(1<<peer):raise Rejected('missing previous hop')
                if packet.key in self.pending or packet.key in self.delivered:raise Rejected('duplicate data')
                if self.id==self.sink:
                    key=self.channel.keys.get(packet.source)
                    if key is None or not hmac.compare_digest(packet.source_tag,hmac.digest(key,SOURCE+packet.immutable(),'sha256')[:TAG]):raise Rejected('source tag')
                    if len(self.delivered)>=self.capacity:raise Rejected('sink record capacity')
                    self.delivered[packet.key]=now+2.;self.delivered_total+=1;msg=RECEIPT.pack(*packet.key);receipt=msg+self.private.sign(SINK+msg);self.accepted.append('sink_data')
                    return [(peer,self.channel.seal(3,peer,receipt))]
                self.accepted.append('transit_data');return self._forward(packet,peer,now)
            if len(body)!=RECEIPT.size+64:raise Rejected('receipt length')
            try:self.public.verify(body[RECEIPT.size:],SINK+body[:RECEIPT.size])
            except InvalidSignature:raise Rejected('sink signature')
            identity=RECEIPT.unpack(body[:RECEIPT.size]);record=self.pending.get(identity)
            if record is None or record.peer!=peer:raise Rejected('receipt route')
            if record.receipt:raise Rejected('duplicate receipt')
            self._settle(record,now,True)
            if not record.receipt:
                record.receipt=True
                if record.acked and not record.credited:self.success_counts[peer]=self.success_counts.get(peer,0)+1;record.credited=True
            self.accepted.append('receipt')
            if record.previous is not None:return [(record.previous,self.channel.seal(3,record.previous,body))]
            return []
        except (Rejected,struct.error) as e:
            reason=str(e);self.rejects[reason]=self.rejects.get(reason,0)+1;return []

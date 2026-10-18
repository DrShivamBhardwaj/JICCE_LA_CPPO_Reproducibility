"""Post-hoc trace diagnostics and causal evidence checks; no radio simulation."""
from pathlib import Path
import collections,gzip,json,re,struct,hashlib
import numpy as np


def read_events(folder):
    folder=Path(folder);p=folder/'COOJA.testlog'
    raw=p.read_bytes() if p.exists() else gzip.decompress((folder/'COOJA.testlog.gz').read_bytes())
    events=[]
    for line in raw.decode().splitlines():
        m=re.match(r'^(\d+) node-(\d+) (\{.*\})$',line)
        if m:
            d=json.loads(m[3]);d['_node']=int(m[2])-1;d['_time_us']=int(m[1]);events.append(d)
    return raw,events


def packet_identity(wire):
    w=bytes.fromhex(wire)
    if len(w)<36: raise ValueError('short envelope')
    kind=w[1];body=w[20:-16]
    if kind==1:return kind,None
    if len(body)<14:raise ValueError('short packet identity')
    return kind,(int.from_bytes(body[:2],'big'),int.from_bytes(body[6:14],'big'),int.from_bytes(body[2:6],'big'))


def causal_audit(events):
    """Check emitted transitions against antecedent wire/ACK events.

    Additional archive audit, not a proof of RF truth or unlogged computations.
    Receipt processing uses ready_ms, not merely radio arrival time.
    """
    transmitted=set();registered={};decisions={};acks={};evidence={};sink_inputs={};source_inputs={}
    counts=collections.Counter()
    for v in events:
        event=v['event'];node=v['_node'];now=v.get('now_ms',v['_time_us']/1000)
        if 'node' in v and v['node']!=node:raise ValueError('node label mismatch')
        if event=='local_tx':
            w=bytes.fromhex(v['wire']);kind,identity=packet_identity(v['wire'])
            if int.from_bytes(w[2:4],'big')!=node or int.from_bytes(w[4:6],'big')!=v['peer']:raise ValueError('TX envelope identity')
            transmitted.add(v['wire'])
            if kind==2:registered[(node,v['peer'],identity[2])] = identity
        elif event in ('cooja_rx','cooja_passive'):
            if v['wire'] not in transmitted:raise ValueError('received wire without antecedent transmission')
            kind,identity=packet_identity(v['wire'])
            if identity is None:continue
            peer=v['peer'];ready=v.get('ready_ms',now)
            if event=='cooja_passive':
                if kind!=2 or identity[2]!=v['pid']:raise ValueError('passive identity')
                evidence[(node,peer,identity[2],'passive')]=(now,identity)
            elif kind in (3,4):
                evidence[(node,peer,identity[2],'receipt' if kind==3 else 'proof')]=(ready,identity)
                if kind==3:source_inputs[(node,identity[2])]=(ready,identity)
            elif kind==2:sink_inputs[(node,identity[2])]=(ready,identity)
        elif event=='local_decision':decisions[(node,v['peer'],v['pid'])]=now
        elif event=='cooja_ack' and v['kind']==2:acks[(node,v['peer'],v['pid'])]=(now,bool(v['ok']))
        elif event=='feedback':
            key=(node,v['peer'],v['pid']);op=v['op']
            if op=='register':
                if key not in decisions or decisions[key]>now:raise ValueError('registration without decision')
            elif op=='ack':
                prior=acks.get(key)
                if prior is None or prior[0]>now or prior[1]!=bool(v['ok']):raise ValueError('feedback ACK without matching MAC result')
            elif op=='evidence':
                prior=evidence.get((*key,v['kind']));identity=registered.get(key)
                if prior is None or prior[0]>now or identity is None or prior[1]!=identity:raise ValueError('unsupported or premature feedback evidence')
            elif op!='expire':raise ValueError('unknown feedback operation')
            counts[op]+=1
        elif event in ('local_sink_delivery','local_receipt'):
            prior=(sink_inputs if event=='local_sink_delivery' else source_inputs).get((node,v['pid']))
            if prior is None or prior[0]>now:raise ValueError('delivery/receipt without processed input')
            counts[event]+=1
    return dict(status='passed_antecedent_event_checks',checks=dict(counts),scope='Temporal and packet-identity provenance; complements rather than replaces wire cryptography, ledger replay and policy audits')


def run_metrics(events,onset=20,attacker=1):
    offered={v['pid']:v['now_ms'] for v in events if v['event']=='cooja_offer'}
    sink={v['pid']:v['now_ms'] for v in events if v['event']=='local_sink_delivery'}
    receipt={v['pid']:v['now_ms'] for v in events if v['event']=='local_receipt' and v['_node']==0}
    choices=[v for v in events if v['event']=='local_decision' and v['_node']==0]
    critical=[p for p in offered if p%3==0];missing=sum(p not in sink for p in critical);late=sum(p in sink and sink[p]-offered[p]>90 for p in critical)
    post=[p for p in offered if p>=onset];postchoices=[v for v in choices if v['pid']>=onset]
    safe=next((v['pid']-onset for v in postchoices if v['peer']!=attacker),None)
    delivery_delays=[sink[p]-offered[p] for p in sorted(sink)];receipt_delays=[receipt[p]-offered[p] for p in sorted(receipt)]
    return dict(offered=len(offered),delivered=len(sink),critical_offered=len(critical),critical_undelivered=missing,critical_delivered_late=late,critical_failure=(missing+late)/len(critical),sink_delay_ms=delivery_delays,source_signed_receipt_delay_ms=receipt_delays,post_attack_offered=len(post),post_attack_delivered=sum(p in sink for p in post),post_attack_losses=sum(p not in sink for p in post),first_safe_choice_packet_offset=safe,first_safe_choice_observed=safe is not None,source_relay_switches=sum(x['peer']!=y['peer'] for x,y in zip(choices,choices[1:])),source_attacker_choices_post=sum(v['peer']==attacker for v in postchoices),adaptation_scope='First safe selection after onset, not sustained recovery; null means right-censored within the offered-packet window')

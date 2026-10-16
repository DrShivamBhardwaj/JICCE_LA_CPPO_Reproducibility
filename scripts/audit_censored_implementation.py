"""Independent endpoint reconstruction; leaves the frozen experiment unchanged."""
import gzip,json,math
from pathlib import Path
import numpy as np
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'outputs/ns3_censored';summary=json.loads((out/'summary.json').read_text());lookup={(r['seed'],r['setting'],r['arm']):r for r in summary};protocol=json.loads((ROOT/'configs/ns3_censored_protocol.json').read_text());settings={s['name']:s for s in protocol['settings']};counts=dict(runs=0,packets=0,beacon_requests=0,mac_handle_rejections=0,ack_failed_after_passive=0,non_source_debt_nonzero=0);qmin=1.;results=[]
for path in sorted(out.glob('trace_*.jsonl.gz')):
 with gzip.open(path,'rt') as stream:
  for line in stream:
   r=json.loads(line);kind=r['type']
   if kind=='run':
    key=(r['seed'],r['setting'],r['arm']);sources=r['sources'];classes=r['classes'];sink=len(r['positions'])-1;delivered={};generated={};beacons=0;decisions=0;passive=set();counts['runs']+=1
   elif kind=='beacon_sent':beacons+=1
   elif kind in ['decision','no_candidate']:
    pid=r['pid'];node=r['node']
    if node==sources[pid] and pid not in generated:generated[pid]=r['time']
    if kind=='decision':
     decisions+=1;raw=r['raw'];pdr=raw['links'].get(str(r['peer']),[9.,1.,.005]);qmin=min(qmin,pdr[0]/sum(pdr[:2]))
     if node not in sources and (any(raw['delay_debt']) or any(raw['loss_debt'])):counts['non_source_debt_nonzero']+=1
   elif kind=='mac':
    if r['kind']==1 and r['node']==sink:delivered.setdefault(r['pid'],r['time'])
    if r['kind']==7:passive.add((r['node'],r['peer'],r['pid']))
    if r['kind']==3 and not r['ok'] and (r['node'],r['peer'],r['pid']) in passive:counts['ack_failed_after_passive']+=1
    if r['kind']==4:counts['mac_handle_rejections']+=1
   elif kind=='final':
    expected=lookup[key];assert len(generated)==60,(key,len(generated))
    bad=sum(pid not in delivered or delivered[pid]-generated[pid]>.09 for pid,c in enumerate(classes) if c==0);nc=classes.count(0);tele=np.array(r['telemetry']);energy=float(tele[:-1,0].sum());delivery=len(delivered)/60.;jpb=energy/(len(delivered)*52) if delivered else None
    computed=dict(delivered=len(delivered),delivery=delivery,critical_violation=bad/nc,radio_energy_j=energy,energy_per_delivered_byte=jpb,beacon_requests=beacons,decisions=decisions)
    for name,value in computed.items():assert np.isclose(value,expected[name],rtol=1e-12,atol=1e-12),(key,name,value,expected[name])
    assert np.allclose(tele[:,6:].sum(1),4.,atol=1e-8);assert np.allclose(3*(.0174*tele[:,6]+.0188*tele[:,7]+.000020*tele[:,8]),tele[:,0],atol=1e-10)
    counts['packets']+=60;counts['beacon_requests']+=beacons;results.append(dict(seed=key[0],setting=key[1],arm=key[2],tx_j=float(3*.0174*tele[:-1,6].sum()),listen_rx_j=float(3*.0188*tele[:-1,7].sum()),off_j=float(3*.000020*tele[:-1,8].sum()),**computed))
assert counts['runs']==750 and counts['packets']==45000
contrasts=[]
for setting in settings:
 for metric in ['radio_energy_j','energy_per_delivered_byte','phy_tx_frames','delivery']:
  a=np.array([lookup[(s,setting,'censored_passive')][metric] for s in range(77001,77031)]);b=np.array([lookup[(s,setting,'active_proof')][metric] for s in range(77001,77031)]);delta=a-b;se=delta.std(ddof=1)/math.sqrt(30);contrasts.append(dict(setting=setting,metric=metric,censored_mean=float(a.mean()),active_mean=float(b.mean()),difference=float(delta.mean()),ci95=[float(delta.mean()-t.ppf(.975,29)*se),float(delta.mean()+t.ppf(.975,29)*se)],status='descriptive audit; no added confirmatory test'))
report=dict(status='passed',counts=counts,minimum_decision_link_success=qmin,endpoint_reconstruction='All 750 final delivery, critical violation, energy, beacon and decision records matched independently reconstructed trace values.',contrasts=contrasts,mean_listen_rx_fraction=float(np.mean([r['listen_rx_j']/r['radio_energy_j'] for r in results])),boundaries=['Shared per-packet visited set and reverse-path map are simulator-side route state; their dissemination cost is not serialized.','Only source nodes update per-class QoS debt from receipt or 1.5-second expiry. Relays can retain zero debt for transit traffic.','Beacon values are simulator metadata gated by actual radio receive events, not serialized energy/queue fields.','Candidate geometry is simulator-provided; training RSSI proxy is replaced by received LQI in transfer.','Four-second always-listening radio model excludes CPU, sensing, cryptography, duty cycling and hardware calibration.','Watch records are retained through a run; expiration scans all records every millisecond. Long-lived bounded-memory operation is not demonstrated.','Active proof semantics can credit a relay without a successful observer first-hop ACK, unlike passive controls; comparison changes semantics and traffic together.','Fractional evidence is clipped on each effective-count update. At expected link success below 0.1, separate half credits can exceed one full weighted credit; no calibrated posterior is claimed.'])
(out/'implementation_audit.json').write_text(json.dumps(report,indent=2));(out/'radio_components.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['contrasts','boundaries']},indent=2))

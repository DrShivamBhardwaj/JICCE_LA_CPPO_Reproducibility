"""Rebind a completed experimental analysis to all captured bytes and case settings."""
from pathlib import Path
import json,gzip,hashlib,xml.etree.ElementTree as E,argparse,re,struct
ROOT=Path(__file__).resolve().parents[1]

def verify_dataset(dataset,protocol_path=None):
    dataset=Path(dataset);protocol_path=Path(protocol_path or ROOT/'experiments/remediation_v1/protocol.json');p=json.loads(protocol_path.read_text());analysis=json.loads((dataset/'analysis.json').read_text());complete=json.loads((dataset/'execution_complete.json').read_text());sha=hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    if analysis['status']!='completed_block_factorial_analysis' or analysis['runs']!=p['expected_runs'] or complete['cases']!=p['expected_runs'] or analysis['protocol_sha256']!=sha or complete['protocol_sha256']!=sha:raise ValueError('incomplete/stale analysis or protocol')
    if {f.name for f in (dataset/'runs').iterdir() if f.is_dir()}!={c['case_id'] for c in p['cases']}:raise ValueError('case coverage mismatch')
    for c in p['cases']:
        f=dataset/'runs'/c['case_id'];a=json.loads((f/'audit.json').read_text())
        if json.loads((f/'case.json').read_text())!=c:raise ValueError('case metadata mismatch')
        if a['status']!='independent_audit_passed' or a['antecedent_provenance']['status']!='passed_antecedent_event_checks':raise ValueError('incomplete per-case audit')
        raw=gzip.decompress((f/'COOJA.testlog.gz').read_bytes());image=gzip.decompress((f/'native_mote.so.gz').read_bytes())
        if hashlib.sha256(raw).hexdigest()!=a['log_sha256'] or hashlib.sha256(image).hexdigest()!=a['native_image_sha256']:raise ValueError('capture/image hash mismatch: '+c['case_id'])
        if int(raw.decode().splitlines()[0].split(':',1)[1])!=c['seed']:raise ValueError('actual simulator seed mismatch')
        for line in raw.decode().splitlines():
            match=re.match(r'^(\d+) node-(\d+) (\{.*\})$',line)
            if not match:continue
            event=json.loads(match[3]);node=int(match[2])-1
            if event['event']=='app_blackhole' and (not c['attacker'] or node!=c['attacker'] or event['pid']<c['onset']):raise ValueError('actual attacker/onset mismatch')
            if event['event']=='cooja_rx':
                wire=bytes.fromhex(event['wire'])
                if wire[1]==1:
                    x,y=struct.unpack('!2f',wire[20:28]);expected=c['positions'][event['peer']]
                    if max(abs(x-expected[0]),abs(y-expected[1]))>1e-5:raise ValueError('received beacon geometry mismatch')

        expected={'mode':c['mode'],'proof':c['proof'],'attack':int(c['attacker']!=0),'timing':c['timing']}
        if a['config']!=expected:raise ValueError('treatment mismatch')
        key=f"outputs/jicce_validation/checkpoints/attention_{c['checkpoint']}.pt"
        if a['checkpoint_sha256']!=p['source_sha256'][key]:raise ValueError('checkpoint mismatch')
        tree=E.parse(f/'simulation.csc');sim=tree.find('simulation')
        if int(sim.findtext('randomseed'))!=c['seed'] or float(sim.findtext('radiomedium/success_ratio_rx'))!=c['rx_probability']:raise ValueError('configuration seed/channel mismatch')
        motes=sim.find('motetype').findall('mote')
        if len(motes)!=4 or [int(m.findtext('.//id')) for m in motes]!=[1,2,3,4]:raise ValueError('mote identity/coverage mismatch')
        for mote,xy in zip(motes,c['positions']):
            pos=mote.find('interface_config/pos')
            if [float(pos.get('x')),float(pos.get('y'))]!=xy:raise ValueError('geometry mismatch')
    return dict(status='passed_complete_archive_integrity',cases=p['expected_runs'],protocol_sha256=sha,logs_images_and_case_settings_verified=True,scope='Integrity and archived audit acceptance; not physical provenance or protection against coordinated archive replacement',physical_validation=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();report=verify_dataset(a.dataset);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

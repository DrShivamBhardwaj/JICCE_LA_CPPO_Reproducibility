"""Evidence-backed completion gate. Fast private receipts never satisfy signed deadlines.

Exit 2 means the requested full-validation scope remains incomplete, not an audit crash.
External physical/security/author evidence requires review; file presence alone is not approval.
"""
from pathlib import Path
import argparse,json,hashlib

def assess(root):
    root=Path(root)
    summary=json.loads((root/'outputs/cc2538_fast/receipt_profiles_summary.json').read_text())
    profiles={}
    for profile in ['cc2538_v2','cc2538_q22','cc2538_fast']:
        rows=[x for x in summary['rows'] if x['profile']==profile]
        if len(rows)!=2 or {x['topology'] for x in rows}!={'chain','choice'}:
            raise ValueError('Incomplete or duplicate topology coverage: '+profile)
        if any(x['offered']!=100 or x['delivered']!=100 or x['ed25519_receipts']!=100 for x in rows):
            raise ValueError('Incomplete packet or signed-proof acceptance: '+profile)
        profiles[profile]={'offered':sum(x['offered'] for x in rows),
            'signed_deadline_misses':sum(x['signed_deadline_misses'] for x in rows)}
        if profile=='cc2538_fast':
            profiles[profile]['fast_private_deadline_misses']=sum(x['fast_deadline_misses'] for x in rows)
    pilot_path=root/'outputs/mcu_deadline_v1/analysis.json'
    pilot=None
    if pilot_path.exists():
        pilot=json.loads(pilot_path.read_text())
        if pilot.get('status')!='completed_compiler_only_pilot' or len(pilot['rows'])!=2 or any(x['offered']!=100 or x['delivered']!=100 or x['signed_receipts']!=100 for x in pilot['rows']):
            raise ValueError('Incomplete O3 diagnostic')
        pilot={'runs':2,'offered':200,'signed_deadline_misses':sum(x['signed_deadline_misses'] for x in pilot['rows']),'physical_validation':False,'scope':'Compiler-only sequential functional diagnostic; no new deadline endpoint'}
    lto_path=root/'outputs/mcu_deadline_v2/analysis.json'
    lto=None
    if lto_path.exists():
        value=json.loads(lto_path.read_text())
        if (value.get('status')!='completed_compiler_only_pilot' or len(value.get('rows',[]))!=2
            or {row['topology'] for row in value['rows']}!={'chain','choice'}
            or any(row['offered']!=100 or row['delivered']!=100 or row['signed_receipts']!=100 for row in value['rows'])):
            raise ValueError('Incomplete LTO diagnostic')
        # Derive deadline failures from retained packet records, not a caller's pass flag.
        misses=0
        for row in value['rows']:
            verification=json.loads((lto_path.parent/(row['topology']+'_100')/'verification.json').read_text())
            packets=verification['emulated_receipt_delays']
            if (verification['status']!='passed' or len(packets)!=100 or len({p['pid'] for p in packets})!=100
                or verification['unique_sink_deliveries']!=100 or verification['unique_source_verified_receipts']!=100):
                raise ValueError('Incomplete LTO packet acceptance')
            derived=sum(p['receipt_delay_ms']>[90,350,1500][p['traffic']] for p in packets)
            if derived!=row['signed_deadline_misses']:raise ValueError('LTO deadline summary mismatch')
            misses+=derived
        lto={'runs':2,'offered':200,'signed_deadline_misses':misses,'physical_validation':False,
             'scope':'Fixed LTO and default loop optimization; unchanged signed endpoint and deadlines'}
    selected=lto or pilot or profiles['cc2538_q22']
    checks=[
      {'id':'original_signed_deadline','complete':selected['signed_deadline_misses']==0,
       'evidence':'outputs/mcu_deadline_v2/analysis.json' if lto else ('outputs/mcu_deadline_v1/analysis.json' if pilot else 'outputs/cc2538_fast/receipt_profiles_summary.json'),
       'reason':'Original signed endpoint; private source MAC is a separate endpoint.'},
      {'id':'physical_rf_energy','complete':False,
       'evidence':'outputs/cc2538_fast/hardware_presence.json',
       'reason':'No acquired physical RF/current trace or reviewed board port; emulation cannot substitute.'},
      {'id':'production_mcu_security','complete':False,
       'reason':'Protected key storage, persistent device sessions, physical provisioning and board-specific security tests not validated.'},
      {'id':'coauthor_approvals','complete':False,
       'reason':'Corresponding-author permissions and equal-contribution/no-competing-interest statements are recorded in Author_permission_register.json. Independent exact-version confirmations and exclusivity/overlap declarations are not asserted.'},
      {'id':'authenticated_submission','complete':False,
       'reason':'Authenticated portal requirements and final assembled submission PDF not independently checked.'}]
    # These hard-false checks are deliberate: this gate must be extended with reviewed
    # real evidence, rather than accepting a caller-controlled completed=true flag.
    extension=root/'outputs/cooja_feedback/primary_600/analysis.json'
    virtual=json.loads(extension.read_text()) if extension.exists() else None
    return {'status':'complete' if all(x['complete'] for x in checks) else 'incomplete',
      'full_validation_complete':all(x['complete'] for x in checks),
      'profiles':profiles,'completed_mcu_o3':pilot,'completed_mcu_lto':lto,'checks':checks,'completed_cooja_extension':{'runs':virtual['runs'],'policy_decisions_verified':virtual['policy_decisions'],'physical_validation':False} if virtual and virtual.get('status')=='passed_paired_seed_analysis' else None,
      'scope':'Retained emulation diagnostics only; no external approval or physical certification inferred.',
      'summary_sha256':hashlib.sha256((root/'outputs/cc2538_fast/receipt_profiles_summary.json').read_bytes()).hexdigest()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=assess(args.root)
    data=json.dumps(report,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(data)
    print(data,end='')
    return 0 if report['full_validation_complete'] else 2
if __name__=='__main__':raise SystemExit(main())

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
    checks=[
      {'id':'original_signed_deadline','complete':profiles['cc2538_q22']['signed_deadline_misses']==0,
       'evidence':'outputs/cc2538_fast/receipt_profiles_summary.json',
       'reason':'Original signed endpoint; private source MAC is a separate endpoint.'},
      {'id':'physical_rf_energy','complete':False,
       'evidence':'outputs/cc2538_fast/hardware_presence.json',
       'reason':'No acquired physical RF/current trace or reviewed board port; emulation cannot substitute.'},
      {'id':'production_mcu_security','complete':False,
       'reason':'Protected key storage, persistent device sessions, physical provisioning and board-specific security tests not validated.'},
      {'id':'coauthor_approvals','complete':False,
       'reason':'Actual final-version approvals and contribution/exclusivity confirmations not supplied; unchecked templates are not consent.'},
      {'id':'authenticated_submission','complete':False,
       'reason':'Authenticated portal requirements and final assembled submission PDF not independently checked.'}]
    # These hard-false checks are deliberate: this gate must be extended with reviewed
    # real evidence, rather than accepting a caller-controlled completed=true flag.
    extension=root/'outputs/cooja_feedback/primary_600/analysis.json'
    virtual=json.loads(extension.read_text()) if extension.exists() else None
    return {'status':'complete' if all(x['complete'] for x in checks) else 'incomplete',
      'full_validation_complete':all(x['complete'] for x in checks),
      'profiles':profiles,'checks':checks,'completed_cooja_extension':{'runs':virtual['runs'],'policy_decisions_verified':virtual['policy_decisions'],'physical_validation':False} if virtual and virtual.get('status')=='passed_paired_seed_analysis' else None,
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

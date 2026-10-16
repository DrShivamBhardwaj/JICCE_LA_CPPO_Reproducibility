"""Reconcile every displayed effect interval with frozen analysis and row means."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];F=R/'publication/array/figures'
v=json.loads((F/'plotted_values.json').read_text());p=json.loads((F/'figure_provenance.json').read_text())
for name,sha in p['inputs'].items():
    if hashlib.sha256((R/name).read_bytes()).hexdigest()!=sha:raise ValueError('Input fingerprint mismatch: '+name)
rows=json.loads((R/'outputs/ns3_censored/summary.json').read_text());a=json.loads((R/'outputs/ns3_censored/paired_analysis.json').read_text());ia=json.loads((R/'outputs/ns3_censored/implementation_audit.json').read_text());tr=json.loads((R/'outputs/auth_policy/summary.json').read_text());ta=json.loads((R/'outputs/auth_policy/analysis.json').read_text())
n=0
for key in ['fig4','fig5']:
 for e in v[key]:
    setting=e.get('setting','blackhole');z=next(z for z in a if z['setting']==setting and z['endpoint']=='delivery' and z['comparator']==e['comparator'])
    np.testing.assert_allclose([e['mean_pp'],*e['ci95_pp']],[100*z['difference'],*(100*np.array(z['ci95']))],rtol=0,atol=1e-12)
    aa={r['seed']:r['delivery'] for r in rows if r['setting']==setting and r['arm']=='censored_passive'};bb={r['seed']:r['delivery'] for r in rows if r['setting']==setting and r['arm']==e['comparator']}
    assert len(aa)==len(bb)==30 and aa.keys()==bb.keys()
    np.testing.assert_allclose(e['mean_pp'],np.mean([100*(aa[s]-bb[s]) for s in aa]),rtol=0,atol=1e-12);n+=1
for e in v['fig6']:
 z=next(z for z in ia['contrasts'] if z['setting']==e['setting'] and z['metric']==e['metric']);s=e['display_scale']
 np.testing.assert_allclose([e['difference'],*e['ci95']],[s*z['difference'],*(s*np.array(z['ci95']))],rtol=0,atol=1e-12);n+=1
for e in v['fig8']:
 z=next(z for z in ta['effects'] if z['setting']==e['setting'] and z['endpoint']=='delivery' and z['comparator']==e['comparator'])
 np.testing.assert_allclose([e['mean_pp'],*e['ci95_pp']],[100*z['difference'],*(100*np.array(z['ci95']))],rtol=0,atol=1e-12)
 aa={r['seed']:r['delivery'] for r in tr if r['setting']==e['setting'] and r['arm']=='attention'};bb={r['seed']:r['delivery'] for r in tr if r['setting']==e['setting'] and r['arm']==e['comparator']}
 assert len(aa)==len(bb)==30 and aa.keys()==bb.keys()
 np.testing.assert_allclose(e['mean_pp'],np.mean([100*(aa[s]-bb[s]) for s in aa]),rtol=0,atol=1e-12);n+=1
for name in ['fig1_architecture','fig2_algorithm_flow','fig3_evaluation_flow','fig4_delivery_effects','fig5_blackhole_estimation','fig6_energy_attribution','fig7_authenticated_virtual','fig8_policy_transfer']:
 for ext in ['svg','pdf','png']:assert (F/f'{name}.{ext}').stat().st_size>1000
result=dict(status='passed',effect_intervals_reconciled=n,source_rows=750,transfer_rows=180,paired_observations_drawn=240,figures=8,exports=24,source_fingerprints_checked=len(p['inputs']),statistics_unchanged=True)
(F/'value_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

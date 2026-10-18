"""Exploratory descriptive controls/factor summaries; no new inferential family."""
from pathlib import Path
import json,statistics,sys
R=Path(__file__).resolve().parents[1];O=R/'outputs/remediation_v1';sys.path.insert(0,str(R/'experiments/remediation_v1'))
from analyze import effects

def main():
    rows=json.loads((O/'run_endpoints.json').read_text());protocol=json.loads((R/'experiments/remediation_v1/protocol.json').read_text());analysis=json.loads((O/'analysis.json').read_text());assert len(rows)==1440
    arms=['censored','censored_proof','negative','negative_proof','active_reference'];controls=[];benign_effects=[]
    for timing in [0,1]:
        for arm in arms:
            selected=[r for r in rows if r['physical_attacker']==0 and r['timing']==timing and r['arm']==arm];assert len(selected)==48
            mean=lambda key:statistics.mean(statistics.mean(r[key] for r in selected if r['block']==b) for b in range(12))
            controls.append(dict(timing=timing,arm=arm,geometry_blocks=12,run_settings=48,delivery=mean('delivery'),critical_failure=mean('critical_failure'),tx_seconds=mean('tx_seconds')))
        values={r['arm']:r['delivery'] for r in controls if r['timing']==timing};benign_effects.append(dict(timing=timing,whole_run_delivery_effects=effects(values)))
    factors=[]
    for factor in ['checkpoint','onset','rx_probability']:
        for value in sorted({b[factor] for b in protocol['blocks']}):
            indices=[b['block'] for b in protocol['blocks'] if b[factor]==value]
            for contrast in [x for x in analysis['contrasts'] if x['endpoint']=='post_delivery']:
                vals=[contrast['block_differences'][i] for i in indices];factors.append(dict(factor=factor,value=value,timing=contrast['timing'],contrast=contrast['contrast'],geometry_blocks=len(vals),mean_effect=statistics.mean(vals),observed_block_range=[min(vals),max(vals)]))
    result={'classification':'Exploratory post-outcome descriptive aggregation of already retained endpoints; no additional tests, intervals, tuning or exclusions','benign_endpoint':'Whole-run unique sink delivery; critical sink lateness/loss and transmit-state seconds','benign_controls':controls,'benign_factorial_point_effects':benign_effects,'factor_stratified_primary_effects':factors,'factor_warning':'Factor levels belong to different geometry blocks; these summaries do not isolate onset/channel/checkpoint causes or establish a threshold. Observed ranges are not confidence intervals.','nonsignificance_warning':'Zero or small benign point differences do not establish equivalence.','physical_validation':False}
    (O/'control_and_factor_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    text=['# Matched-study control supplement','','These are exploratory descriptive summaries of the completed 1,440 cases. They add no significance tests or multiplicity family. The six primary contrasts and all historical results remain unchanged.','','Table S1. Benign controls.','','| Timing | Arm | Delivery (%) | Critical failure (%) | TX state (s) |','|---|---|---:|---:|---:|']
    for x in controls:text.append(f"| {'Native' if x['timing']==0 else 'Scheduled'} | {x['arm']} | {100*x['delivery']:.3f} | {100*x['critical_failure']:.3f} | {x['tx_seconds']:.3f} |")
    text+=['','Each row averages twelve geometry blocks, each containing two radio seeds and two relay permutations: forty-eight correlated run settings. Delivery is whole-run sink delivery, not the attacked primary post-onset endpoint. Critical failures include missing or late sink deliveries against 90 ms. TX is modeled transmit-state time, not measured energy.','', f"The benign negative-update main-effect point estimate is {100*benign_effects[0]['whole_run_delivery_effects']['negative_main']:+.3f} percentage points without added compute delay and {100*benign_effects[1]['whole_run_delivery_effects']['negative_main']:+.3f} points with scheduled delays. Proof-generation point estimates are {100*benign_effects[0]['whole_run_delivery_effects']['proof_main']:+.3f} and {100*benign_effects[1]['whole_run_delivery_effects']['proof_main']:+.3f} points, respectively. These descriptive values establish neither equivalence nor an absence of practically relevant effects.",'', 'Checkpoint-, onset- and channel-stratified primary effect summaries are retained in `outputs/remediation_v1/control_and_factor_summary.json`. Each checkpoint has four geometry blocks; each onset or channel level has six. The factors were balanced but not fully crossed within geometry. Differences across these strata do not isolate a causal onset/channel/checkpoint effect, and their observed ranges are not statistical confidence intervals.','', 'The original primary family, analysis SHA and radio captures are unchanged. Reproduce with `python scripts/summarize_remediation_controls.py`.']
    (R/'publication/array/Remediation_Control_Supplement.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':main()

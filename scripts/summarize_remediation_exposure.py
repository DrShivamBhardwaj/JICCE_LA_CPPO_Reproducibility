"""Explicitly exploratory post-outcome stratification; never changes primary contrasts."""
from pathlib import Path
import json,statistics
R=Path(__file__).resolve().parents[1];O=R/'outputs/remediation_v1'
def main():
    rows=json.loads((O/'secondary_run_diagnostics.json').read_text());result=[]
    for timing in [0,1]:
        for arm in ['censored','censored_proof','negative','negative_proof','active_reference']:
            selected=[r for r in rows if r['timing']==timing and r['arm']==arm and r['physical_attacker']!=0 and r['last_pre_onset_choice_attacker']];observed=[r for r in selected if r['sustained_start'] is not None]
            result.append(dict(timing=timing,arm=arm,previously_attacker=len(selected),right_censored=len(selected)-len(observed),recovered_within_20=sum(r['recovered_within_20'] for r in selected),conditional_median_confirmation_ms=statistics.median(r['sustained_confirmation_ms'] for r in observed) if observed else None,conditional_median_start_opportunities=statistics.median(r['sustained_start'] for r in observed) if observed else None))
    report={'classification':'Exploratory post-outcome aggregation stratifying the declared recovery metric by last pre-onset source choice; no new test, tuning, exclusion or change to primary analysis','scope':'Correlated run-setting counts; conditional medians exclude right-censored settings and do not prove safe downstream paths','groups':result};(O/'exposure_summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

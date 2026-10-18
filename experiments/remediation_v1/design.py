"""Generate a prospective, balanced remediation design before new outcomes."""
from pathlib import Path
import json,random,hashlib
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
ARMS={'censored':(0,0),'censored_proof':(0,1),'negative':(2,0),'negative_proof':(2,1),'active_reference':(1,1)}

def generate():
    rng=random.Random(951018);blocks=[];cases=[]
    for checkpoint in [41001,41002,41003]:
        for onset,rx in [(10,.9),(10,1.),(30,.9),(30,1.)]:
            block=len(blocks);positions=[[0.,0.],[45+rng.uniform(-1,1),15+rng.uniform(-1,1)],[45+rng.uniform(-1,1),-15+rng.uniform(-1,1)],[90.,0.]]
            blocks.append(dict(block=block,checkpoint=checkpoint,onset=onset,rx_probability=rx,physical_positions=positions))
            for radio in [0,1]:
                seed=95001+2*block+radio
                for permutation in [0,1]:
                    xy=[positions[0],positions[1+permutation],positions[2-permutation],positions[3]]
                    for physical_attacker in [0,1,2]:
                        attacker=0 if not physical_attacker else (physical_attacker if not permutation else 3-physical_attacker)
                        for timing in [0,1]:
                            for arm,(mode,proof) in ARMS.items():
                                case=dict(block=block,checkpoint=checkpoint,onset=onset,rx_probability=rx,radio=radio,seed=seed,permutation=permutation,physical_attacker=physical_attacker,attacker=attacker,timing=timing,arm=arm,mode=mode,proof=proof,positions=xy)
                                case['case_id']=f'b{block:02d}_r{radio}_p{permutation}_a{physical_attacker}_t{timing}_{arm}';cases.append(case)
    return blocks,cases


def freeze():
    blocks,cases=generate()
    protocol=dict(classification='Prospective remediation study informed by archived results; separate from every historical statistical family',starting_commit='f9bf3c9382c73cee2f21fffa94e07f1a0affe415',expected_runs=len(cases),independent_geometry_blocks=12,checkpoints=[41001,41002,41003],radio_seeds_per_block=2,packets=60,interval_s=.3,arms=ARMS,blocks=blocks,cases=cases,matched_controls={'own_ACK_gate':True,'expiry_ms_after_ACK':150,'positive_evidence':'passive .5 or signed receipt 1; proofs excluded from matched-arm credit','positive_weight':'same original incremental clip(expected*delta,.05,1)','late_positive_evidence':'accepted for both matched rules after successful own ACK until slot reuse','negative_rule':'one expected-weight failure increment on expiry without positive evidence when enabled'},reference_scope='Original active semantics retained as reference, not a matched negative-rule intervention',statistical_plan={'unit':'Independent geometry block; average the two radio seeds and paired permutations/attacker positions within each block','primary_endpoint':'Post-onset unique sink delivery fraction in attacked runs','primary_contrasts':'negative-update main effect, proof-generation main effect, difference-in-differences interaction; each at timing 0 and 1','multiplicity':'One 6-contrast Holm family for primary delivery; separate 6-contrast families for critical failure and transmit-state seconds','CI':'Pointwise paired cluster bootstrap over 12 geometry blocks, 20000 draws, RNG 951019','tests':'Two-sided exhaustive sign-flip over 12 block differences, 4096 assignments, conditional on symmetric block effects; no claim of randomized treatment assignment','secondary':'Benign summaries, active-reference contrasts, adaptation, onset/channel/checkpoint interactions descriptive/exploratory, not pooled confirmatory tests','practical_margin':'No noninferiority or equivalence claim; report effects and pointwise intervals without invented deployment margins','adaptation':'First three consecutive safe source selections after attack onset; report right censoring and recovery within 20 packet opportunities','limits':'Checkpoint/onset/channel are balanced block factors, not fully crossed within each geometry. Three retained checkpoints and a narrow geometry family do not identify a universal threshold.'},timing_scope='Native host execution or illustrative per-packet scheduled delays; no serial CPU service/physical calibration',energy_scope='Energest transmit/listen seconds only; no measured joules',security_scope='Public fixture-key tests; no deployment confidentiality/protected key storage claim',execution_policy='Technical preflight excluded. Retain all declared cases and failures; no outcome-based retries/exclusions. Stop incomplete on infrastructure/audit failures.',contiki_commit='4ccd1a3b9e767f168d12ec3df187fe6b7dc736b5',cooja_commit='fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4')
    dependencies=list(D.glob('*.py'))+[D/'bootstrap.sh',R/'.github/workflows/wsn-remediation.yml',R/'tests/test_remediation_v1.py',R/'scripts/audit_cooja_feedback_quantized.py',R/'src/wsn_sim/censored_feedback.py',R/'src/wsn_sim/security.py',R/'src/wsn_sim/auth_policy.py',R/'src/wsn_sim/rl.py',R/'outputs/cooja_feedback/primary_600/runs.json',R/'outputs/cooja_feedback/primary_600/analysis.json']+[R/'hardware/cooja_feedback/feedback.c',R/'hardware/cooja_feedback/feedback_ledger.h',R/'hardware/cooja_feedback/local_feedback.h',R/'hardware/cooja_feedback/Makefile',R/'hardware/cooja_feedback/pilot.csc',R/'hardware/cooja_feedback/project-conf.h',R/'hardware/cooja_feedback/cooja-radio-observer.patch',R/'hardware/cc2538_q22/actor.h']+[R/f'outputs/jicce_validation/checkpoints/attention_{x}.pt' for x in protocol['checkpoints']]
    protocol['source_sha256']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}
    target=D/'protocol.json'
    if target.exists():raise SystemExit('Freeze exists; refuse replacement')
    target.write_text(json.dumps(protocol,indent=2)+'\n');print('Frozen cases',len(cases))
if __name__=='__main__':freeze()

"""Verify completeness and reproduce paired analyses from stored seed summaries."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from run_jicce_validation import analyse

root=Path(__file__).resolve().parents[1]
p=root/'outputs/jicce_validation'
s=pd.read_csv(p/'seed_summary.csv')
episode_path=p/'episode_metrics.csv'
if not episode_path.exists():episode_path=p/'episode_metrics.csv.gz'
e=pd.read_csv(episode_path)
assert len(s)==480 and len(e)==115200
assert not s.duplicated(['seed','policy','setting']).any()
assert e.groupby(['seed','policy','setting']).size().eq(240).all()
assert len(list((p/'checkpoints').glob('*.pt')))==120
assert set(s.seed)==set(range(41001,41031))
delivery=e.groupby(['seed','policy','setting']).delivered.mean()
observed=s.set_index(['seed','policy','setting']).delivery_rate
assert np.allclose(delivery.sort_index(),observed.sort_index(),atol=1e-12)
new=analyse(s)
saved=pd.read_csv(p/'paired_analysis.csv')
for col in ['mean_difference','ci95_low','ci95_high','paired_t_p','holm_primary_p']:
    assert np.allclose(new[col],saved[col],equal_nan=True,atol=1e-12),col
print('PASS: 480 complete seed-setting rows; 115200 packet records; 120 checkpoints; delivery and paired analyses reproduced')

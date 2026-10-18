from pathlib import Path
import sys,struct,numpy as np
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'scripts'))
from audit_cooja_feedback_quantized import features,FeedbackLedger

def state(now):
 c=np.zeros((4,11),np.float32)
 for peer,stamp,y in [(1,16.05,15),(2,16.60,-15)]:c[peer]=[45,y,1,0,stamp,100/255,9,1,.005,0,1]
 return dict(now_ms=now,created_ms=now,traffic=2,visited=1,cache_hex=struct.pack('!44f',*c.ravel()).hex(),qos_hex=struct.pack('!6f',*([0]*6)).hex())

def test_float32_timestamp_truncation_excludes_751ms_candidate():
 _,ids=features(state(16800),0,FeedbackLedger(4,'censored'))
 assert ids==[2]

def test_750ms_integer_boundary_remains_eligible():
 _,ids=features(state(16799),0,FeedbackLedger(4,'censored'))
 assert ids==[1,2]

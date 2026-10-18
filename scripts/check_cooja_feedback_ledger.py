"""Compile and replay critical C ledger edge cases against the retained Python reference."""
from pathlib import Path
import subprocess,json,sys
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'src'))
from wsn_sim.censored_feedback import FeedbackLedger
source='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
static unsigned node_id=0,feedback_mode;static uint32_t milliseconds;
static float clip(float x,float a,float b){return x<a?a:x>b?b:x;}
#include "feedback_ledger.h"
int main(void){
 for(feedback_mode=0;feedback_mode<4;feedback_mode++){
  memset(watches,0,sizeof watches);for(unsigned p=0;p<4;p++){feedback_a[p]=1;feedback_b[p]=1;}
  milliseconds=0;feedback_register(0,1,1,.9f);
  milliseconds=10;feedback_evidence(1,1,.5f,"passive");
  milliseconds=20;feedback_ack(0,1);
  milliseconds=180;feedback_expire();
  milliseconds=300;feedback_evidence(1,1,1.f,"receipt");
  milliseconds=301;feedback_evidence(1,1,1.f,"receipt");
  milliseconds=302;feedback_evidence(1,1,1.f,"proof");
  milliseconds=500;feedback_register(1,2,2,.8f);
  milliseconds=510;feedback_ack(1,0);
  milliseconds=520;feedback_evidence(2,2,.5f,"passive");
  milliseconds=700;feedback_expire();
  printf("SUMMARY %u %.9g %.9g %.9g %.9g\\n",feedback_mode,feedback_a[1],feedback_b[1],feedback_a[2],feedback_b[2]);
 }
 return 0;
}'''
b=r/'build';b.mkdir(exist_ok=True);(b/'ledger_crosscheck.c').write_text(source);subprocess.run(['cc','-O2','-I'+str(r/'hardware/cooja_feedback'),str(b/'ledger_crosscheck.c'),'-o',str(b/'ledger_crosscheck')],check=True);output=subprocess.check_output([str(b/'ledger_crosscheck')],text=True);reports=[]
for line in output.splitlines():
 if not line.startswith('SUMMARY '):continue
 _,mode,*counts=line.split();mode=int(mode);ledger=FeedbackLedger(4,['censored','active','naive','frozen'][mode]);ledger.register(0,1,1,0,.9);ledger.evidence(0,1,1,'passive',.01);ledger.acknowledge(0,1,1,True,.02);ledger.expire(.18);ledger.evidence(0,1,1,'receipt',.3);ledger.evidence(0,1,1,'receipt',.301);ledger.evidence(0,1,1,'proof',.302);ledger.register(0,2,2,.5,.8);ledger.acknowledge(0,2,2,False,.51);ledger.evidence(0,2,2,'passive',.52);ledger.expire(.7);expected=[ledger.risk[0].a[1],ledger.risk[0].b[1],ledger.risk[0].a[2],ledger.risk[0].b[2]];assert max(abs(float(a)-b) for a,b in zip(counts,expected))<1e-6;reports.append({'mode':mode,'counts':list(map(float,counts))})
assert len(reports)==4
out=r/'outputs/cooja_feedback/ledger_crosscheck.json';out.write_text(json.dumps(dict(status='passed',cases=['pre_ACK_passive','ACK_gate','expiry','late_upgrade','deduplication','failed_first_hop','active_proof_only','frozen_counts'],modes=reports),indent=2)+'\n');print(out.read_text())

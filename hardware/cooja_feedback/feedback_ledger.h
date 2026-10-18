/* Port of FeedbackLedger, retained for two-second local pending lifetime. */
static float feedback_a[4]={1,1,1,1},feedback_b[4]={1,1,1,1};
static struct {unsigned used,peer,pid,closed,timed_out;int acked;uint32_t expiry;float expected,seen,credited;} watches[16];
static void feedback_log(const char*op,unsigned i,const char*kind,int ok){
 printf("{\"event\":\"feedback\",\"op\":\"%s\",\"node\":%u,\"peer\":%u,\"pid\":%u,\"now_ms\":%u,\"expected\":%.9g,\"kind\":\"%s\",\"ok\":%d,\"a\":%.9g,\"b\":%.9g,\"seen\":%.9g,\"credited\":%.9g}\n",op,node_id,watches[i].peer,watches[i].pid,milliseconds,watches[i].expected,kind,ok,feedback_a[watches[i].peer],feedback_b[watches[i].peer],watches[i].seen,watches[i].credited);
}
static void feedback_credit(unsigned i){
 if(feedback_mode==3||(watches[i].acked!=1&&feedback_mode!=1))return;
 float delta=watches[i].seen-watches[i].credited;if(delta<=0)return;
 feedback_a[watches[i].peer]+=clip(watches[i].expected*delta,.05f,1.f);watches[i].credited=watches[i].seen;
}
static void feedback_register(unsigned i,unsigned peer,unsigned pid,float expected){
 memset(&watches[i],0,sizeof watches[i]);if(peer==3)return;
 watches[i].used=1;watches[i].peer=peer;watches[i].pid=pid;watches[i].expected=expected;watches[i].acked=-1;watches[i].expiry=feedback_mode==1?milliseconds+150:0;feedback_log("register",i,"",-1);
}
static void feedback_ack(unsigned i,int ok){
 if(!watches[i].used)return;watches[i].acked=ok!=0;
 if(feedback_mode!=1){if(ok){watches[i].expiry=milliseconds+150;feedback_credit(i);}else watches[i].closed=1;}
 feedback_log("ack",i,"",ok!=0);
}
static void feedback_evidence(unsigned pid,unsigned peer,float strength,const char*kind){
 for(unsigned i=0;i<16;i++)if(watches[i].used&&watches[i].pid==pid&&watches[i].peer==peer){
  if((feedback_mode==1&&strcmp(kind,"proof"))||(feedback_mode!=1&&!strcmp(kind,"proof")))return;
  if(watches[i].closed&&(feedback_mode!=0||watches[i].acked!=1))return;
  if(strength>watches[i].seen)watches[i].seen=strength;feedback_credit(i);feedback_log("evidence",i,kind,1);return;
 }
}
static void feedback_expire(void){
 for(unsigned i=0;i<16;i++)if(watches[i].used&&!watches[i].closed&&watches[i].expiry&&(int32_t)(milliseconds-watches[i].expiry)>=0){
  watches[i].closed=1;
  if(watches[i].seen<=0){watches[i].timed_out=1;if(feedback_mode==1||feedback_mode==2)feedback_b[watches[i].peer]+=clip(watches[i].expected,.05f,1.f);}
  feedback_log("expire",i,"",0);
 }
}
static void feedback_snapshot(void){printf("{\"event\":\"feedback_snapshot\",\"node\":%u,\"a\":[%.9g,%.9g,%.9g,%.9g],\"b\":[%.9g,%.9g,%.9g,%.9g]}\n",node_id,feedback_a[0],feedback_a[1],feedback_a[2],feedback_a[3],feedback_b[0],feedback_b[1],feedback_b[2],feedback_b[3]);}

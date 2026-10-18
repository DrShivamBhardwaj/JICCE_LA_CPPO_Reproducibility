extern uint32_t _bss_end;
static void stack_paint(void){uintptr_t sp;__asm__ volatile("mov %0, sp":"=r"(sp));for(volatile uint32_t*p=&_bss_end;(uintptr_t)p+64<sp;p++)*p=0xa5a5a5a5u;}
static void stack_report(void){
 volatile uint32_t*p=&_bss_end;unsigned guard=1;
 for(unsigned j=0;j<16;j++)if(p[j]!=0xa5a5a5a5u)guard=0;
 while((uintptr_t)p<0x20008000u&&*p==0xa5a5a5a5u)p++;
 text(",\"observed_stack_bytes\":");number(0x20008000u-(uintptr_t)p);
 text(",\"static_ram_bytes\":");number((uintptr_t)&_bss_end-0x20000000u);
 text(guard?",\"stack_guard\":true":",\"stack_guard\":false");
}
/* Four-node emulated pilot with trusted UART provisioning. No production-board claim. */
static void command(const char*);
static unsigned mode_attention=1,local_enabled=0,local_seq,last_pid=0xffffffffu;
static unsigned delivered_count,receipt_count,reject_count;
static uint8_t provision_keys[4][32],sink_seed[32],sink_pub[32];static uint64_t boot_sessions[4];static unsigned provisioned;static uint8_t sink_secret_cached[64];
static void secret_wipe(void*p,unsigned n){volatile uint8_t*x=p;while(n--)*x++=0;}
static uint64_t pair_session(unsigned n){return boot_sessions[n];}
static uint16_t u16(const uint8_t*p){return (uint16_t)((p[0]<<8)|p[1]);}
static uint32_t u32(const uint8_t*p){return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
static uint64_t u64(const uint8_t*p){return ((uint64_t)u32(p)<<32)|u32(p+4);}
static void w16(uint8_t*p,unsigned n){p[0]=n>>8;p[1]=n;}
static void w32(uint8_t*p,uint32_t n){for(int i=3;i>=0;i--){p[i]=n;n>>=8;}}
static void w64(uint8_t*p,uint64_t n){w32(p,n>>32);w32(p+4,(uint32_t)n);}
static void wf(uint8_t*p,float f){union{float f;uint32_t u;}v={.f=f};w32(p,v.u);}
static float rf(const uint8_t*p){union{float f;uint32_t u;}v={.u=u32(p)};return v.f;}
static int equal(const uint8_t*a,const uint8_t*b,unsigned n){unsigned d=0;for(unsigned i=0;i<n;i++)d|=a[i]^b[i];return d==0;}
static void profile(const char*stage,unsigned start){text("{\"event\":\"stage_time\",\"node\":");number(node_id);text(",\"stage\":\"");text(stage);text("\",\"elapsed_ms\":");number(milliseconds-start);text("}\n");}
static void mac(uint8_t*out,unsigned peer,const uint8_t*domain,unsigned dn,const uint8_t*msg,unsigned n){
 unsigned started=milliseconds;uint8_t block[64]={0},inner[32];SHA256_CTX c;
 unsigned lo=node_id<peer?node_id:peer,hi=node_id<peer?peer:node_id;
 for(unsigned i=0;i<32;i++)block[i]=provision_keys[peer][i];
 for(unsigned i=0;i<64;i++)block[i]^=0x36;
 sha256_init(&c);sha256_update(&c,block,64);sha256_update(&c,domain,dn);sha256_update(&c,msg,n);sha256_final(&c,inner);
 for(unsigned i=0;i<64;i++)block[i]^=0x36^0x5c;
 sha256_init(&c);sha256_update(&c,block,64);sha256_update(&c,inner,32);sha256_final(&c,out);secret_wipe(block,sizeof block);secret_wipe(inner,sizeof inner);secret_wipe(&c,sizeof c);profile("hmac",started);
}
static const uint8_t hop_domain[]="JICCE-hop-v1",source_domain[]="JICCE-source-v1",sink_domain[]="JICCE-sink-v1";
static struct {unsigned seen,highest;uint64_t bits;} replay[4];
static struct {unsigned valid,seq;float x,y,e,q,stamp,lqi,a,b,delay;unsigned success;} cache[4];
static struct {unsigned used,pid,source,previous,peer,token,acked,receipt,credited,settled,traffic;uint64_t session;uint32_t created,expires,sent;} pending_live[16];
static struct {unsigned seen,highest;uint64_t bits;} source_replay[4];static float debts_live[6];
static unsigned live_tx_counter=10000;static unsigned fast_seen[16];
static const uint8_t fast_domain[]="JICCE-fast-sink-v1";
static void event(const char*s,unsigned pid,unsigned peer){text("{\"event\":\"");text(s);text("\",\"node\":");number(node_id);text(",\"pid\":");number(pid);text(",\"peer\":");number(peer);text(",\"now_ms\":");number(milliseconds);text("}\n");}
static void reject(const char*why){reject_count++;text("{\"event\":\"reject\",\"reason\":\"");text(why);text("\"}\n");}
static unsigned send_wire(unsigned kind,unsigned peer,const uint8_t*payload,unsigned n,unsigned pid){
 uint8_t wire[114],tag[32];if(n+36>114||peer>=4||local_seq==0xffffffffu){reject("send_bounds");return 0;}
 wire[0]=1;wire[1]=kind;w16(wire+2,node_id);w16(wire+4,peer);w64(wire+6,pair_session(node_id));w32(wire+14,local_seq++);w16(wire+18,n);memcpy(wire+20,payload,n);
 mac(tag,peer,hop_domain,sizeof hop_domain,wire,n+20);memcpy(wire+n+20,tag,16);
 text("{\"event\":\"local_tx\",\"peer\":");number(peer);text(",\"wire\":\"");for(unsigned i=0;i<n+36;i++)bytehex(wire[i]);text("\"}\n");
 /* Reuse the tested bounded FIFO driver, not host routing or host crypto. */
 char line[340];unsigned z=0;const char*start="{\"wire\":\"";while(*start)line[z++]=*start++;
 for(unsigned i=0;i<n+36;i++){line[z++]=hex[wire[i]>>4];line[z++]=hex[wire[i]&15];}
 const char*mid="\",\"token\":";while(*mid)line[z++]=*mid++;
 unsigned token=++live_tx_counter;char dec[12];unsigned k=0,t=token;do{dec[k++]='0'+t%10;t/=10;}while(t);while(k)line[z++]=dec[--k];
 mid=",\"peer\":";while(*mid)line[z++]=*mid++;line[z++]='0'+peer;line[z++]='}';line[z]=0;
 command(line);(void)pid;return token;
}
static float sqroot(float x){if(x<=0)return 0;float y=x>1?x:1;for(int i=0;i<12;i++)y=.5f*(y+x/y);return y;}
static float clip(float x,float lo,float hi){return x<lo?lo:x>hi?hi:x;}
static float own_x,own_y;static const float limits[3]={.09f,.35f,1.5f};
static void emit_floats(const float*x,unsigned n){for(unsigned i=0;i<n;i++){union{float f;uint32_t u;}v={.f=x[i]};for(int j=7;j>=0;j--)put(hex[(v.u>>(4*j))&15]);}}
static void settle_live(unsigned i,unsigned delivered){
 if(pending_live[i].settled)return;unsigned c=pending_live[i].traffic;float elapsed=(milliseconds-pending_live[i].created)*.001f;
 static const float budgets[6]={.015f,.01f,.04f,.03f,.1f,.08f};
 debts_live[2*c]=clip(debts_live[2*c]+(float)(!delivered||elapsed>limits[c])-budgets[2*c],0,1e6f);
 debts_live[2*c+1]=clip(debts_live[2*c+1]+(float)!delivered-budgets[2*c+1],0,1e6f);pending_live[i].settled=1;
}
static void local_ack(unsigned token,int ok){
 if(!local_enabled)return;
 for(unsigned i=0;i<16;i++)if(pending_live[i].used&&pending_live[i].token==token){
  unsigned p=pending_live[i].peer;pending_live[i].acked=ok!=0;cache[p].a+=(float)(ok!=0);cache[p].b+=(float)(ok==0);
  cache[p].delay=.8f*cache[p].delay+.2f*(milliseconds-pending_live[i].sent)*.001f;
  if(ok&&pending_live[i].receipt&&!pending_live[i].credited){cache[p].success++;pending_live[i].credited=1;}
  event(ok?"local_mac_ok":"local_mac_failed",pending_live[i].pid,p);break;
 }
}
static void forward_live(uint8_t*body,unsigned n,unsigned previous){
 unsigned now=milliseconds;unsigned source=u16(body),pid=u32(body+2),traffic=body[14];uint64_t session=u64(body+6);
 if(body[23]>=22||body[24+12]&(1u<<node_id)){reject("loop_hops");return;}
 body[23]++;body[36]|=1u<<node_id;
 float obs[93]={0},score[8]={0},rows[8][10]={{0}},current=sqroot((own_x-90)*(own_x-90)+own_y*own_y);unsigned ids[8],count=0;unsigned char mask[8]={0};
 for(unsigned p=0;p<4;p++){
  if(!cache[p].valid||now-(unsigned)(cache[p].stamp*1000)>750||cache[p].e<=0||(body[36]&(1u<<p)))continue;
  float distance=sqroot((cache[p].x-90)*(cache[p].x-90)+cache[p].y*cache[p].y),progress=current-distance;if(progress<=0)continue;
  float pdr=cache[p].a/(cache[p].a+cache[p].b),ta=1+cache[p].success*pdr,risk=.75f/(ta+1),ucb=clip(risk+1.645f*.75f*sqroot(ta/((ta+1)*(ta+1)*(ta+2))),0,1);
  float row[10]={(float)(p==3),cache[p].e,pdr,cache[p].lqi,cache[p].q,clip(progress/38,-1,1),p==3?0:risk,p==3?0:ucb,clip(1/pdr-1,0,4)/4,clip(cache[p].delay/limits[traffic],0,2)/2};
  float value=1.25f*progress/38+.75f*pdr+.25f*cache[p].e-.55f*row[7]-.2f*cache[p].q;
  unsigned j=count++;while(j&&(value>score[j-1]||(value==score[j-1]&&p<ids[j-1]))){score[j]=score[j-1];ids[j]=ids[j-1];memcpy(rows[j],rows[j-1],sizeof row);j--;}
  score[j]=value;ids[j]=p;memcpy(rows[j],row,sizeof row);
 }
 if(!count){reject("no_fresh_progress");return;}
 obs[0]=1;obs[2]=clip(current/212.132034356f,0,1);obs[3]=clip(1-(now-(unsigned)(u64(body+15)/1000))*.001f/limits[traffic],0,1);obs[4+traffic]=1;
 for(unsigned i=0;i<6;i++)obs[7+i]=debts_live[i]/(1+debts_live[i]);
 for(unsigned i=0;i<count;i++){mask[i]=1;memcpy(obs+13+10*i,rows[i],40);}
 unsigned actor_start=milliseconds;float logits[8];int selected=mode_attention?actor(obs,mask,logits):0;profile("actor",actor_start);if(selected<0){reject("actor_input_bounds");return;}
 unsigned peer=ids[selected],slot=16;
 for(unsigned i=0;i<16;i++){
  if(pending_live[i].used&&pending_live[i].pid==pid&&pending_live[i].source==source&&pending_live[i].session==session){reject("duplicate_data");return;}
  if(!pending_live[i].used&&slot==16)slot=i;
 }
 if(slot==16){reject("pending_capacity");return;}
 fast_seen[slot]=0;pending_live[slot].used=1;pending_live[slot].pid=pid;pending_live[slot].source=source;pending_live[slot].session=session;pending_live[slot].previous=previous;pending_live[slot].peer=peer;pending_live[slot].traffic=traffic;pending_live[slot].created=(unsigned)(u64(body+15)/1000);pending_live[slot].expires=now+2000;pending_live[slot].sent=now;
 text("{\"event\":\"local_decision\",\"pid\":");number(pid);text(",\"peer\":");number(peer);text(",\"ids\":[");for(unsigned i=0;i<count;i++){if(i)put(',');number(ids[i]);}text("]");text(",\"now_ms\":");number(now);text(",\"created_ms\":");number((unsigned)(u64(body+15)/1000));text(",\"traffic\":");number(traffic);text(",\"visited\":");number(body[36]);text(",\"cache_hex\":\"");for(unsigned p=0;p<4;p++){float values[11]={cache[p].x,cache[p].y,cache[p].e,cache[p].q,cache[p].stamp,cache[p].lqi,cache[p].a,cache[p].b,cache[p].delay,(float)cache[p].success,(float)cache[p].valid};emit_floats(values,11);}text("\",\"qos_hex\":\"");emit_floats(debts_live,6);text("\",\"obs_hex\":\"");emit_floats(obs,93);text("\",\"logits_hex\":\"");if(mode_attention)emit_floats(logits,8);text("\"}\n");
 pending_live[slot].token=send_wire(2,peer,body,n,pid);
}
static void receive_live(const uint8_t*wire,unsigned n,unsigned mac_peer){
 if(!local_enabled)return;
 if(n<36||n>114||mac_peer>=4){reject("wire_length");return;}
 unsigned kind=wire[1],sender=u16(wire+2),size=u16(wire+18),seq=u32(wire+14);
 if(wire[0]!=1||kind<1||kind>4||sender!=mac_peer||u16(wire+4)!=node_id||sender==node_id||size+36!=n){reject("envelope");return;}
 uint8_t tag[32];mac(tag,sender,hop_domain,sizeof hop_domain,wire,n-16);
 if(!equal(tag,wire+n-16,16)){reject("tag");return;}
 if(u64(wire+6)!=pair_session(sender)){reject("session");return;}
 if(replay[sender].seen&&seq<=replay[sender].highest){unsigned delta=replay[sender].highest-seq;if(delta>=64||(replay[sender].bits&((uint64_t)1<<delta))){reject("replay");return;}replay[sender].bits|=(uint64_t)1<<delta;}
 else {unsigned gap=seq-replay[sender].highest;replay[sender].bits=(!replay[sender].seen||gap>=64)?1:(replay[sender].bits<<gap)|1;replay[sender].highest=seq;replay[sender].seen=1;}
 uint8_t body[78];memcpy(body,wire+20,size);
 if(kind==1){
  if(size!=22){reject("beacon_length");return;}
  float x=rf(body),y=rf(body+4),e=rf(body+8);uint64_t stamp=u64(body+14),now=(uint64_t)milliseconds*1000;
  if(stamp>now+1000||now>stamp+750000||!(x>=-10000&&x<=10000&&y>=-10000&&y<=10000&&e>=0&&e<=1)){reject("beacon_values_age");return;}
  if(cache[sender].valid&&seq<=cache[sender].seq){reject("older_beacon");return;}
  cache[sender].valid=1;cache[sender].seq=seq;cache[sender].x=x;cache[sender].y=y;cache[sender].e=e;cache[sender].q=u16(body+12);cache[sender].stamp=(float)stamp/1e6f;cache[sender].lqi=100.f/255;
  event("local_beacon",0,sender);return;
 }
 if(kind==2){
  if(size<54||body[37]>24||size!=54u+body[37]||u16(body)>=4||body[14]>=3||body[23]>22){reject("data_bounds");return;}
  unsigned source=u16(body),pid=u32(body+2);uint64_t now=(uint64_t)milliseconds*1000,created=u64(body+15);
  if(u64(body+6)!=pair_session(source)||created>now+1000||now>created+2000000||(body[36]&(1u<<node_id))||!(body[36]&(1u<<sender))){reject("data_age_loop");return;}
  if(node_id!=3){forward_live(body,size,sender);return;}
  uint8_t immutable[48];memcpy(immutable,body,23);immutable[23]=body[37];memcpy(immutable+24,body+38,body[37]);mac(tag,source,source_domain,sizeof source_domain,immutable,24+body[37]);
  if(!equal(tag,body+38+body[37],16)){reject("source_tag");return;}
  if(source_replay[source].seen&&pid<=source_replay[source].highest){unsigned delta=source_replay[source].highest-pid;if(delta>=64||(source_replay[source].bits&((uint64_t)1<<delta))){reject("sink_duplicate");return;}source_replay[source].bits|=(uint64_t)1<<delta;}
  else {unsigned gap=pid-source_replay[source].highest;source_replay[source].bits=(!source_replay[source].seen||gap>=64)?1:(source_replay[source].bits<<gap)|1;source_replay[source].highest=pid;source_replay[source].seen=1;}
  delivered_count++;event("local_sink_delivery",pid,sender);
  uint8_t fast[30];memcpy(fast,body,14);mac(tag,source,fast_domain,sizeof fast_domain,fast,14);memcpy(fast+14,tag,16);send_wire(4,sender,fast,30,pid);
  uint8_t receipt[78],msg[28];memcpy(receipt,body,14);memcpy(msg,sink_domain,sizeof sink_domain);memcpy(msg+sizeof sink_domain,receipt,14);
  unsigned sign_start=milliseconds;crypto_ed25519_sign(receipt+14,sink_secret_cached,msg,sizeof sink_domain+14);profile("sign",sign_start);send_wire(3,sender,receipt,78,pid);return;
 }
 if(kind==4){
  if(size!=30||u16(body)!=0){reject("fast_length_source");return;}
  if(node_id==0){mac(tag,3,fast_domain,sizeof fast_domain,body,14);if(!equal(tag,body+14,16)){reject("fast_sink_tag");return;}}
  for(unsigned i=0;i<16;i++)if(pending_live[i].used&&pending_live[i].source==u16(body)&&pending_live[i].pid==u32(body+2)&&pending_live[i].session==u64(body+6)){
   if(pending_live[i].peer!=sender||fast_seen[i]){reject("fast_route_duplicate");return;}fast_seen[i]=1;
   if(node_id==0){settle_live(i,1);event("local_fast_receipt",u32(body+2),sender);}
   else send_wire(4,pending_live[i].previous,body,30,u32(body+2));
   /* No positive forwarding credit is assigned from this opaque relay proof. */
   return;
  }
  reject("fast_route");return;
 }
 if(size!=78){reject("receipt_length");return;}
 uint8_t msg[28];memcpy(msg,sink_domain,sizeof sink_domain);memcpy(msg+sizeof sink_domain,body,14);
 unsigned verify_start=milliseconds;int verify_result=crypto_ed25519_check(body+14,sink_pub,msg,sizeof sink_domain+14);profile("verify",verify_start);if(verify_result){reject("sink_signature");return;}
 for(unsigned i=0;i<16;i++)if(pending_live[i].used&&pending_live[i].source==u16(body)&&pending_live[i].pid==u32(body+2)&&pending_live[i].session==u64(body+6)){
  if(pending_live[i].peer!=sender||pending_live[i].receipt){reject("receipt_route_duplicate");return;}
  pending_live[i].receipt=1;settle_live(i,1);if(pending_live[i].acked&&!pending_live[i].credited){cache[sender].success++;pending_live[i].credited=1;}
  receipt_count++;event("local_receipt",u32(body+2),sender);if(pending_live[i].previous!=65535)send_wire(3,pending_live[i].previous,body,78,u32(body+2));return;
 }
 reject("receipt_route");
}
static void local_expire(void){for(unsigned i=0;i<16;i++)if(pending_live[i].used&&(int32_t)(milliseconds-pending_live[i].expires)>=0){settle_live(i,0);memset(&pending_live[i],0,sizeof pending_live[i]);}}
static int local_command(const char*s){
 if(find(s,"provision_material")){
  if(provisioned){reject("reprovision");return 1;}
  const char*p=field(s,"\"material\"");uint8_t data[224];unsigned n=0;
  if(!p||*p++!='\"'){reject("provision_format");return 1;}
  while(*p&&*p!='\"') {int a=digit(*p++);if(!*p||*p=='\"'){reject("provision_format");return 1;}int b=digit(*p++);if(a<0||b<0||n>=224){reject("provision_format");return 1;}data[n++]=(uint8_t)(16*a+b);}
  if(n!=224||*p!='\"'){reject("provision_format");return 1;}
  memcpy(provision_keys,data,128);memcpy(sink_seed,data+128,32);memcpy(sink_pub,data+160,32);for(unsigned i=0;i<4;i++)boot_sessions[i]=u64(data+192+8*i);
  for(unsigned i=0;i<4;i++){if(!boot_sessions[i]){reject("provision_session");return 1;}for(unsigned j=0;j<i;j++)if(boot_sessions[i]==boot_sessions[j]){reject("provision_session");return 1;}}
  if(node_id==3){uint8_t public_check[32];crypto_ed25519_key_pair(sink_secret_cached,public_check,sink_seed);if(!equal(public_check,sink_pub,32)){secret_wipe(data,sizeof data);secret_wipe(provision_keys,sizeof provision_keys);secret_wipe(sink_secret_cached,sizeof sink_secret_cached);reject("provision_key_mismatch");return 1;}}
  secret_wipe(sink_seed,sizeof sink_seed);provisioned=1;secret_wipe(data,sizeof data);event("provisioned",0,0);return 1;
 }

 if(find(s,"local_start")){if(!provisioned){reject("unprovisioned");return 1;}if(local_enabled){reject("session_reuse");return 1;}local_enabled=1;own_x=(float)decimal(field(s,"\"x\""));own_y=(float)decimal(field(s,"\"y\""));for(unsigned p=0;p<4;p++){cache[p].a=9;cache[p].b=1;cache[p].delay=.005f;}event("local_started",0,0);return 1;}
 if(!local_enabled)return 0;
 if(find(s,"local_beacon")){unsigned peer=decimal(field(s,"\"peer\""));uint8_t b[22];wf(b,own_x);wf(b+4,own_y);wf(b+8,1);w16(b+12,0);w64(b+14,(uint64_t)milliseconds*1000);send_wire(1,peer,b,22,0);return 1;}
 if(find(s,"originate")){
  unsigned pid=decimal(field(s,"\"pid\""));if(node_id!=0||pid==0xffffffffu||(last_pid!=0xffffffffu&&pid<=last_pid)){reject("source_counter");return 1;}last_pid=pid;
  uint8_t b[70]={0},imm[40],tag[32];w16(b,node_id);w32(b+2,pid);w64(b+6,pair_session(node_id));b[14]=pid%3;w64(b+15,(uint64_t)milliseconds*1000);b[37]=16;memcpy(b+38,"0123456789abcdef",16);memcpy(imm,b,23);imm[23]=16;memcpy(imm+24,b+38,16);mac(tag,3,source_domain,sizeof source_domain,imm,40);memcpy(b+54,tag,16);forward_live(b,70,65535);return 1;
 }
 if(find(s,"local_status")){text("{\"event\":\"local_status\",\"delivered\":");number(delivered_count);text(",\"receipts\":");number(receipt_count);text(",\"rejects\":");number(reject_count);stack_report();text("}\n");return 1;}
 return 0;
}

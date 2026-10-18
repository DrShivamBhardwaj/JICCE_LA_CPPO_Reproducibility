/* CC2538 Renode register-level radio/UART bridge. Emulation target only.
 * This pilot performs live routing and cryptography on the emulated MCU. No physical power claim.
 */
#include <stdint.h>
#define REG(a) (*(volatile uint32_t *)(a))
#define RF(o) REG(0x40088000u+(o))
#define UART_DR REG(0x4000c000u)
#define UART_FR REG(0x4000c018u)
static void receive_live(const uint8_t*,unsigned,unsigned);
static void local_ack(unsigned,int);
volatile uint32_t node_id;
volatile uint32_t milliseconds;
volatile uint32_t tx_frames,rx_frames,ack_frames;
static uint8_t sequence;
static uint32_t tokens[256],expires[256];
void SysTick_Handler(void){milliseconds++;}
void Default_Handler(void){for(;;){}}
void Reset_Handler(void);
__attribute__((section(".vectors"),used)) const uintptr_t vectors[16]={
 0x20008000u,(uintptr_t)Reset_Handler,(uintptr_t)Default_Handler,
 (uintptr_t)Default_Handler,0,0,0,0,0,0,0,0,0,0,0,(uintptr_t)SysTick_Handler};
void *memcpy(void *d,const void *s,unsigned n){uint8_t *a=d;const uint8_t*b=s;while(n--)*a++=*b++;return d;}
void *memset(void *d,int c,unsigned n){uint8_t*a=d;while(n--)*a++=(uint8_t)c;return d;}
static void put(char c){while(UART_FR&32u){}UART_DR=(uint8_t)c;}
static void text(const char*s){while(*s)put(*s++);}
static void number(uint32_t n){char b[11];unsigned i=0;do{b[i++]=(char)('0'+n%10u);n/=10u;}while(n);while(i)put(b[--i]);}
static const char hex[]="0123456789abcdef";
static void bytehex(uint8_t v){put(hex[v>>4]);put(hex[v&15]);}
static void ack(uint32_t token,int ok){local_ack(token,ok);text("{\"event\":\"ack\",\"token\":");number(token);text(ok?",\"ok\":true}\n":",\"ok\":false}\n");}
static const char *find(const char*s,const char*k){for(;*s;s++){const char*a=s,*b=k;while(*b&&*a==*b){a++;b++;}if(!*b)return a;}return 0;}
static const char *field(const char*s,const char*k){const char*p=find(s,k);if(!p)return 0;while(*p&&*p!=':')p++;if(!*p)return 0;p++;while(*p==' '||*p=='\t')p++;return p;}
static uint32_t decimal(const char*p){uint32_t v=0;if(!p)return 0;while(*p>='0'&&*p<='9'){v=v*10u+(uint32_t)(*p++-'0');}return v;}
static int digit(char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return -1;}
static void radio_rx(void){
 while(RF(0x66c)>0){
  unsigned len=RF(0x828);uint8_t frame[127];
  if(len>127){RF(0x838)=0xed;return;}
  for(unsigned i=0;i<len;i++)frame[i]=(uint8_t)RF(0x828);
  if(len>=5&&(frame[0]&7u)==2u){unsigned seq=frame[2];if(tokens[seq]){ack(tokens[seq],1);tokens[seq]=0;ack_frames++;}}
  else if(len>=11&&(frame[0]&7u)==1u){
   unsigned peer=(unsigned)frame[7]+256u*frame[8];if(!peer)continue;
   rx_frames++;text("{\"event\":\"rx\",\"peer\":");number(peer-1);text(",\"lqi\":100,\"wire\":\"");
   for(unsigned i=9;i<len-2;i++)bytehex(frame[i]);text("\"}\n");
   receive_live(frame+9,len-11,peer-1);
  }
 }
}
#include <stddef.h>
#include "sha256.h"
#include "monocypher-ed25519.h"
#include "actor_vectors.h"
static void emit(const char*s){text(s);}
int memcmp(const void*a,const void*b,size_t n){const unsigned char*x=a,*y=b;for(size_t i=0;i<n;i++)if(x[i]!=y[i])return x[i]-y[i];return 0;}
static void hex32(uint32_t x){char s[10];const char*d="0123456789abcdef";for(int i=0;i<8;i++)s[i]=d[(x>>(28-4*i))&15];s[8]=' ';s[9]=0;emit(s);}
static void hexbytes(const uint8_t*b,unsigned n){for(unsigned i=0;i<n;i++){char s[3];const char*d="0123456789abcdef";s[0]=d[b[i]>>4];s[1]=d[b[i]&15];s[2]=0;emit(s);}emit("\n");}
static float fast_tanh(float x){
 float a=x<0?-x:x;if(a>10.f)return x<0?-1.f:1.f;
 float z=-2.f*a;int n=(int)(z*1.4426950408889634f-.5f);
 float r=z-n*.6931471805599453f;
 float e=1.f,term=1.f;
 for(int i=1;i<=10;i++){term*=r/(float)i;e+=term;}
 union{uint32_t u;float f;}scale;scale.u=(uint32_t)(127+n)<<23;e*=scale.f;
 float t=(1.f-e)/(1.f+e);return x<0?-t:t;
}
static void linear(const float*x,int in,int out,const float*w,const float*b,float*y,int activation){
 for(int j=0;j<out;j++){float sum=b?b[j]:0.f;for(int i=0;i<in;i++)sum+=w[j*in+i]*x[i];y[j]=activation?fast_tanh(sum):sum;}
}
static int actor(const float*obs,const unsigned char*mask,float*logit){
 float a[96],b[96],q[96],c[96],d[96],k[96],bias[48],value[1];
 linear(obs,13,96,ctx_encoder_0_weight,ctx_encoder_0_bias,a,1);
 linear(a,96,96,ctx_encoder_2_weight,ctx_encoder_2_bias,b,1);
 linear(b,96,96,query_weight,0,q,0);
 int best=-1;
 for(int v=0;v<8;v++){if(!mask[v]){logit[v]=-1.e9f;continue;}
  linear(obs+13+v*10,10,96,cand_encoder_0_weight,cand_encoder_0_bias,c,1);
  linear(c,96,96,cand_encoder_2_weight,cand_encoder_2_bias,d,1);
  linear(d,96,96,key_weight,0,k,0);
  linear(d,96,48,actor_bias_0_weight,actor_bias_0_bias,bias,1);
  linear(bias,48,1,actor_bias_2_weight,actor_bias_2_bias,value,0);
  float dot=0;for(int j=0;j<96;j++)dot+=q[j]*k[j];
  logit[v]=mask[v]?dot*.10206207261596575f+value[0]:-1.e9f;
  if(mask[v]&&(best<0||logit[v]>logit[best]))best=v;
 }
 return best;
}
static void hmac_sha256(uint8_t out[32]){
 uint8_t block[64]={0},inner[32];SHA256_CTX ctx;
 for(int i=0;i<20;i++)block[i]=hmac_key[i];
 for(int i=0;i<64;i++)block[i]^=0x36;
 sha256_init(&ctx);sha256_update(&ctx,block,64);sha256_update(&ctx,hmac_message,sizeof hmac_message);sha256_final(&ctx,inner);
 for(int i=0;i<64;i++)block[i]^=0x36^0x5c;
 sha256_init(&ctx);sha256_update(&ctx,block,64);sha256_update(&ctx,inner,32);sha256_final(&ctx,out);
}
/* Four-node emulated live-path pilot. Public test keys only. */
static void command(const char*);
static unsigned mode_attention=1,local_enabled=0,local_seq,last_pid=0xffffffffu;
static unsigned delivered_count,receipt_count,reject_count;
static unsigned pair_session(unsigned n){return 1000u+n;}
static uint16_t u16(const uint8_t*p){return (uint16_t)((p[0]<<8)|p[1]);}
static uint32_t u32(const uint8_t*p){return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
static uint64_t u64(const uint8_t*p){return ((uint64_t)u32(p)<<32)|u32(p+4);}
static void w16(uint8_t*p,unsigned n){p[0]=n>>8;p[1]=n;}
static void w32(uint8_t*p,uint32_t n){for(int i=3;i>=0;i--){p[i]=n;n>>=8;}}
static void w64(uint8_t*p,uint64_t n){w32(p,n>>32);w32(p+4,(uint32_t)n);}
static void wf(uint8_t*p,float f){union{float f;uint32_t u;}v={.f=f};w32(p,v.u);}
static float rf(const uint8_t*p){union{float f;uint32_t u;}v={.u=u32(p)};return v.f;}
static int equal(const uint8_t*a,const uint8_t*b,unsigned n){unsigned d=0;for(unsigned i=0;i<n;i++)d|=a[i]^b[i];return d==0;}
static void mac(uint8_t*out,unsigned peer,const uint8_t*domain,unsigned dn,const uint8_t*msg,unsigned n){
 uint8_t block[64]={0},inner[32];SHA256_CTX c;
 unsigned lo=node_id<peer?node_id:peer,hi=node_id<peer?peer:node_id;
 for(unsigned i=0;i<32;i++)block[i]=(uint8_t)(17+lo*4+hi); /* public deterministic TEST key */
 for(unsigned i=0;i<64;i++)block[i]^=0x36;
 sha256_init(&c);sha256_update(&c,block,64);sha256_update(&c,domain,dn);sha256_update(&c,msg,n);sha256_final(&c,inner);
 for(unsigned i=0;i<64;i++)block[i]^=0x36^0x5c;
 sha256_init(&c);sha256_update(&c,block,64);sha256_update(&c,inner,32);sha256_final(&c,out);
}
static const uint8_t hop_domain[]="JICCE-hop-v1",source_domain[]="JICCE-source-v1",sink_domain[]="JICCE-sink-v1";
static struct {unsigned seen,highest;uint64_t bits;} replay[4];
static struct {unsigned valid,seq;float x,y,e,q,stamp,lqi,a,b,delay;unsigned success;} cache[4];
static struct {unsigned used,pid,source,previous,peer,token,acked,receipt,credited,settled,traffic;uint64_t session;uint32_t created,expires,sent;} pending_live[16];
static unsigned seen_pid[16],seen_used[16];static float debts_live[6];
static unsigned live_tx_counter=10000;
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
 float logits[8];int selected=mode_attention?actor(obs,mask,logits):0;
 unsigned peer=ids[selected],slot=16;
 for(unsigned i=0;i<16;i++){
  if(pending_live[i].used&&pending_live[i].pid==pid&&pending_live[i].source==source&&pending_live[i].session==session){reject("duplicate_data");return;}
  if(!pending_live[i].used&&slot==16)slot=i;
 }
 if(slot==16){reject("pending_capacity");return;}
 pending_live[slot].used=1;pending_live[slot].pid=pid;pending_live[slot].source=source;pending_live[slot].session=session;pending_live[slot].previous=previous;pending_live[slot].peer=peer;pending_live[slot].traffic=traffic;pending_live[slot].created=(unsigned)(u64(body+15)/1000);pending_live[slot].expires=now+2000;pending_live[slot].sent=now;
 text("{\"event\":\"local_decision\",\"pid\":");number(pid);text(",\"peer\":");number(peer);text(",\"ids\":[");for(unsigned i=0;i<count;i++){if(i)put(',');number(ids[i]);}text("]");text(",\"now_ms\":");number(now);text(",\"created_ms\":");number((unsigned)(u64(body+15)/1000));text(",\"traffic\":");number(traffic);text(",\"visited\":");number(body[36]);text(",\"cache_hex\":\"");for(unsigned p=0;p<4;p++){float values[11]={cache[p].x,cache[p].y,cache[p].e,cache[p].q,cache[p].stamp,cache[p].lqi,cache[p].a,cache[p].b,cache[p].delay,(float)cache[p].success,(float)cache[p].valid};emit_floats(values,11);}text("\",\"qos_hex\":\"");emit_floats(debts_live,6);text("\",\"obs_hex\":\"");emit_floats(obs,93);text("\",\"logits_hex\":\"");if(mode_attention)emit_floats(logits,8);text("\"}\n");
 pending_live[slot].token=send_wire(2,peer,body,n,pid);
}
static void receive_live(const uint8_t*wire,unsigned n,unsigned mac_peer){
 if(!local_enabled)return;
 if(n<36||n>114||mac_peer>=4){reject("wire_length");return;}
 unsigned kind=wire[1],sender=u16(wire+2),size=u16(wire+18),seq=u32(wire+14);
 if(wire[0]!=1||kind<1||kind>3||sender!=mac_peer||u16(wire+4)!=node_id||sender==node_id||size+36!=n){reject("envelope");return;}
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
  for(unsigned i=0;i<16;i++)if(seen_used[i]&&seen_pid[i]==pid){reject("sink_duplicate");return;}
  unsigned slot=16;for(unsigned i=0;i<16;i++)if(!seen_used[i]){slot=i;break;}if(slot==16){reject("sink_capacity");return;}seen_used[slot]=1;seen_pid[slot]=pid;
  uint8_t receipt[78],msg[28],seed[32],secret[64],pub[32];memcpy(receipt,body,14);memcpy(msg,sink_domain,sizeof sink_domain);memcpy(msg+sizeof sink_domain,receipt,14);for(unsigned i=0;i<32;i++)seed[i]=42;
  crypto_ed25519_key_pair(secret,pub,seed);crypto_ed25519_sign(receipt+14,secret,msg,sizeof sink_domain+14);delivered_count++;event("local_sink_delivery",pid,sender);send_wire(3,sender,receipt,78,pid);return;
 }
 if(size!=78){reject("receipt_length");return;}
 uint8_t msg[28];memcpy(msg,sink_domain,sizeof sink_domain);memcpy(msg+sizeof sink_domain,body,14);
 if(crypto_ed25519_check(body+14,test_public,msg,sizeof sink_domain+14)){reject("sink_signature");return;}
 for(unsigned i=0;i<16;i++)if(pending_live[i].used&&pending_live[i].source==u16(body)&&pending_live[i].pid==u32(body+2)&&pending_live[i].session==u64(body+6)){
  if(pending_live[i].peer!=sender||pending_live[i].receipt){reject("receipt_route_duplicate");return;}
  pending_live[i].receipt=1;settle_live(i,1);if(pending_live[i].acked&&!pending_live[i].credited){cache[sender].success++;pending_live[i].credited=1;}
  receipt_count++;event("local_receipt",u32(body+2),sender);if(pending_live[i].previous!=65535)send_wire(3,pending_live[i].previous,body,78,u32(body+2));return;
 }
 reject("receipt_route");
}
static void local_expire(void){for(unsigned i=0;i<16;i++)if(pending_live[i].used&&(int32_t)(milliseconds-pending_live[i].expires)>=0){settle_live(i,0);memset(&pending_live[i],0,sizeof pending_live[i]);}}
static int local_command(const char*s){
 if(find(s,"local_start")){if(local_enabled){reject("session_reuse");return 1;}local_enabled=1;own_x=(float)decimal(field(s,"\"x\""));own_y=(float)decimal(field(s,"\"y\""));for(unsigned p=0;p<4;p++){cache[p].a=9;cache[p].b=1;cache[p].delay=.005f;}event("local_started",0,0);return 1;}
 if(!local_enabled)return 0;
 if(find(s,"local_beacon")){unsigned peer=decimal(field(s,"\"peer\""));uint8_t b[22];wf(b,own_x);wf(b+4,own_y);wf(b+8,1);w16(b+12,0);w64(b+14,(uint64_t)milliseconds*1000);send_wire(1,peer,b,22,0);return 1;}
 if(find(s,"originate")){
  unsigned pid=decimal(field(s,"\"pid\""));if(node_id!=0||pid==0xffffffffu||(last_pid!=0xffffffffu&&pid<=last_pid)){reject("source_counter");return 1;}last_pid=pid;
  uint8_t b[70]={0},imm[40],tag[32];w16(b,node_id);w32(b+2,pid);w64(b+6,pair_session(node_id));b[14]=pid%3;w64(b+15,(uint64_t)milliseconds*1000);b[37]=16;memcpy(b+38,"0123456789abcdef",16);memcpy(imm,b,23);imm[23]=16;memcpy(imm+24,b+38,16);mac(tag,3,source_domain,sizeof source_domain,imm,40);memcpy(b+54,tag,16);forward_live(b,70,65535);return 1;
 }
 if(find(s,"local_status")){text("{\"event\":\"local_status\",\"delivered\":");number(delivered_count);text(",\"receipts\":");number(receipt_count);text(",\"rejects\":");number(reject_count);text("}\n");return 1;}
 return 0;
}

static void command(const char*s){
 if(local_command(s))return;
 if(find(s,"telemetry")){unsigned pending=0;for(unsigned i=0;i<256;i++)pending+=tokens[i]!=0;text("{\"event\":\"telemetry\",\"energy_fraction\":1.0,\"queue\":");number(pending);text(",\"provenance\":\"emulated_no_power_model\"}\n");return;}
 const char*p=field(s,"\"wire\"");uint32_t token=decimal(field(s,"\"token\"")),peer=decimal(field(s,"\"peer\""));
 if(!p||*p++!='\"'||!token||peer>=104u){ack(token,0);return;}
 uint8_t data[114];unsigned n=0;
 while(*p&&*p!='\"'){
  int a=digit(*p++);if(!*p||*p=='\"'){ack(token,0);return;}int b=digit(*p++);
  if(a<0||b<0||n>=114){ack(token,0);return;}data[n++]=(uint8_t)(a*16+b);
 }
 if(!n||*p!='\"'){ack(token,0);return;}
 uint8_t seq=sequence++;if(tokens[seq]){ack(token,0);return;}
 tokens[seq]=token;expires[seq]=milliseconds+200u;
 RF(0x838)=0xee;RF(0x828)=n+11u;
 uint8_t header[9]={0x61,0x88,seq,0x34,0x12,(uint8_t)(peer+1u),0,(uint8_t)(node_id+1u),0};
 for(unsigned i=0;i<9;i++)RF(0x828)=header[i];
 for(unsigned i=0;i<n;i++)RF(0x828)=data[i];
 tx_frames++;RF(0x838)=0xe9;RF(0x838)=0xe3;
}
void Reset_Handler(void){
 mode_attention=1;last_pid=0xffffffffu;live_tx_counter=10000;
 REG(0x4000c02cu)=0x60u; /* UART 8-bit words */
 REG(0x4000c030u)=0x301u; /* UART enable, RX and TX */
 RF(0x5c8)=0x34;RF(0x5cc)=0x12;RF(0x5d0)=node_id+1u;RF(0x5d4)=0;
 RF(0x624)=0x60;RF(0x600)=0x0d;RF(0x604)=0x78;RF(0x608)=0;RF(0x63c)=11;
 RF(0x838)=0xed;RF(0x838)=0xee;RF(0x838)=0xe3;
 REG(0xe000e014u)=999;REG(0xe000e018u)=0;REG(0xe000e010u)=7;
 text("{\"event\":\"ready\",\"node\":");number(node_id);text("}\n");
 char line[768];unsigned used=0;int overflow=0;
 for(;;){
  radio_rx();local_expire();
  for(unsigned i=0;i<256;i++)if(tokens[i]&&(int32_t)(milliseconds-expires[i])>=0){ack(tokens[i],0);tokens[i]=0;}
  if(!(UART_FR&16u)){
   char c=(char)UART_DR;
   if(c=='\n'){line[used]=0;if(!overflow)command(line);else text("{\"event\":\"error\",\"reason\":\"line_capacity\"}\n");used=0;overflow=0;}
   else if(c!='\r'){if(used+1<sizeof(line))line[used++]=c;else overflow=1;}
  }
 }
}

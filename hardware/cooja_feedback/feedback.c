/* Native Cooja port; public fixture keys, scheduled delay assumptions, not hardware. */
#include "contiki.h"
#include "net/netstack.h"
#include "net/nullnet/nullnet.h"
#include "net/packetbuf.h"
#include "net/mac/mac.h"
#include "net/mac/framer/frame802154.h"
#include "dev/serial-line.h"
#include "sys/energest.h"
#include "sys/ctimer.h"
#include "sha256.h"
#include "monocypher-ed25519.h"
#include "actor.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
PROCESS(feedback_process,"Frozen policy and feedback comparison");AUTOSTART_PROCESSES(&feedback_process);
static unsigned app_id,feedback_mode,proof_enabled,attack_enabled,timing_mode,configured;
#define node_id app_id
#define milliseconds ((uint32_t)clock_time())
static void put(char c){putchar(c);}static void text(const char*s){printf("%s",s);}static void number(uint32_t n){printf("%u",n);}static const char hex[]="0123456789abcdef";
static void bytehex(uint8_t v){printf("%02x",v);}
static const char*find(const char*s,const char*k){const char*p=strstr(s,k);return p?p+strlen(k):NULL;}
static const char*field(const char*s,const char*k){const char*p=find(s,k);if(!p)return NULL;p=strchr(p,':');if(!p)return NULL;for(p++;*p==' ';p++){};return p;}
static uint32_t decimal(const char*p){uint32_t v=0;if(!p)return 0;while(*p>='0'&&*p<='9'){v=v*10+*p++-'0';}return v;}
static int digit(char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;}
static void command(const char*);
#include "local_feedback.h"
static const int xy[4][2]={{0,0},{45,15},{45,-15},{90,0}};
static struct {unsigned used,started,peer,token,n;uint32_t ready;uint8_t data[114];} jobs[48];
static unsigned queue_overflows,mac_attempts,mac_failures,raw_observations,rx_queue_overflows;
static struct {unsigned used,peer,n;uint32_t ready;uint8_t data[114];} inbox[32];
static void tx_done(void*ptr,int status,int transmissions){
 unsigned i=(unsigned)(uintptr_t)ptr;mac_attempts+=transmissions;mac_failures+=status!=MAC_TX_OK;
 printf("{\"event\":\"cooja_ack\",\"node\":%u,\"token\":%u,\"peer\":%u,\"kind\":%u,\"pid\":%u,\"ok\":%d,\"transmissions\":%d,\"now_ms\":%u}\n",node_id,jobs[i].token,jobs[i].peer,jobs[i].data[1],jobs[i].n>=42?u32(jobs[i].data+22):0,status==MAC_TX_OK,transmissions,milliseconds);
 local_ack(jobs[i].token,status==MAC_TX_OK);jobs[i].used=0;
}
static void command(const char*s){
 const char*p=field(s,"\"wire\"");unsigned token=decimal(field(s,"\"token\"")),peer=decimal(field(s,"\"peer\""));
 if(!p||*p++!='\"'||peer>=4)return;
 unsigned i;for(i=0;i<48&&jobs[i].used;i++){};if(i==48){queue_overflows++;local_ack(token,0);return;}
 jobs[i].used=1;jobs[i].started=0;jobs[i].peer=peer;jobs[i].token=token;jobs[i].n=0;
 while(*p&&*p!='\"'&&jobs[i].n<114){int a=digit(*p++),b=digit(*p++);if(a<0||b<0){jobs[i].used=0;return;}jobs[i].data[jobs[i].n++]=a*16+b;}
 unsigned kind=jobs[i].data[1];jobs[i].ready=milliseconds+(timing_mode?(kind==2?14:1):0);
}
static void input(const void*data,uint16_t n,const linkaddr_t*src,const linkaddr_t*dest){
 (void)dest;if(n<36||n>114||src->u8[0]<1||src->u8[0]>4)return;unsigned i;for(i=0;i<32&&inbox[i].used;i++){};
 if(i==32){rx_queue_overflows++;return;}
 inbox[i].used=1;inbox[i].peer=src->u8[0]-1;inbox[i].n=n;memcpy(inbox[i].data,data,n);
 unsigned kind=inbox[i].data[1];inbox[i].ready=milliseconds+(timing_mode?(kind==3?81:(kind==2&&node_id==3?31:1)):0);
 printf("{\"event\":\"cooja_rx\",\"node\":%u,\"peer\":%u,\"now_ms\":%u,\"ready_ms\":%u,\"wire\":\"",node_id,inbox[i].peer,milliseconds,inbox[i].ready);for(unsigned k=0;k<n;k++)bytehex(inbox[i].data[k]);text("\"}\n");
}
void app_observe_raw(const void*raw,unsigned n){
 if(!configured||!local_enabled)return;frame802154_t f;
 if(!frame802154_parse((uint8_t*)raw,n,&f)||f.fcf.frame_type!=FRAME802154_DATAFRAME||f.payload_len<90)return;
 const uint8_t*w=f.payload;unsigned len=f.payload_len;if(w[0]!=1||w[1]!=2||len>114||u16(w+18)+36!=len)return;
 unsigned sender=u16(w+2),dest=u16(w+4);if(sender>=4||dest>=4||sender==node_id||dest==node_id)return;
 /* Public fixture link keys permit validation of captured envelopes here. This
  * is not a deployment key-distribution or compromised-node security claim. */
 uint8_t key[32],block[64]={0},inner[32],tag[32];SHA256_CTX c;
 for(unsigned k=0;k<32;k++)key[k]=(uint8_t)(17*k+13*(sender<dest?sender:dest)+7*(sender>dest?sender:dest));
 memcpy(block,key,32);for(unsigned k=0;k<64;k++)block[k]^=0x36;
 sha256_init(&c);sha256_update(&c,block,64);sha256_update(&c,hop_domain,sizeof hop_domain);sha256_update(&c,w,len-16);sha256_final(&c,inner);
 for(unsigned k=0;k<64;k++)block[k]^=0x36^0x5c;sha256_init(&c);sha256_update(&c,block,64);sha256_update(&c,inner,32);sha256_final(&c,tag);
 if(!equal(tag,w+len-16,16))return;
 raw_observations++;printf("{\"event\":\"cooja_passive\",\"node\":%u,\"peer\":%u,\"pid\":%u,\"now_ms\":%u,\"wire\":\"",node_id,sender,u32(w+22),milliseconds);for(unsigned k=0;k<len;k++)bytehex(w[k]);text("\"}\n");
 feedback_evidence(u32(w+22),sender,.5f,"passive");
}
static void initialize(void){
 uint8_t seed[32],pub[32],sk[64];for(unsigned i=0;i<32;i++)seed[i]=i+1;crypto_ed25519_key_pair(sk,pub,seed);
 for(unsigned peer=0;peer<4;peer++){for(unsigned k=0;k<32;k++)provision_keys[peer][k]=(uint8_t)(17*k+13*(node_id<peer?node_id:peer)+7*(node_id>peer?node_id:peer));boot_sessions[peer]=1000+peer;}
 memcpy(sink_pub,pub,32);if(node_id==3)memcpy(sink_secret_cached,sk,64);memset(sk,0,64);provisioned=1;own_x=xy[node_id][0];own_y=xy[node_id][1];local_enabled=1;
 for(unsigned peer=0;peer<4;peer++){cache[peer].a=9;cache[peer].b=1;cache[peer].delay=.005;}
}
PROCESS_THREAD(feedback_process,ev,data){
 static struct etimer timer;static unsigned pid,done;
 PROCESS_BEGIN();app_id=linkaddr_node_addr.u8[0]-1;nullnet_set_input_callback(input);etimer_set(&timer,CLOCK_SECOND/1000);
 while(1){
  PROCESS_WAIT_EVENT();
  if(ev==serial_line_event_message){unsigned mode,proof,attack,timing;if(sscanf((const char*)data,"CONFIG %u %u %u %u",&mode,&proof,&attack,&timing)==4&&!configured&&mode<4&&proof<2&&attack<2&&timing<2){feedback_mode=mode;proof_enabled=proof;attack_enabled=attack;timing_mode=timing;configured=1;initialize();printf("{\"event\":\"configured\",\"node\":%u,\"mode\":%u,\"proof\":%u,\"attack\":%u,\"timing\":%u}\n",node_id,mode,proof,attack,timing);}}
  if(!configured||!etimer_expired(&timer))continue;
  for(unsigned i=0;i<32;i++)if(inbox[i].used&&(int32_t)(milliseconds-inbox[i].ready)>=0){receive_live(inbox[i].data,inbox[i].n,inbox[i].peer);inbox[i].used=0;}
  local_expire();
  /* Staggered periodic authenticated beacon unicasts; no geometry/attack labels enter observations. */
  if(milliseconds>=1000&&milliseconds<26000&&milliseconds%500==node_id*50){for(unsigned peer=0;peer<4;peer++)if(peer!=node_id){char msg[64];snprintf(msg,sizeof msg,"{\"local_beacon\":1,\"peer\":%u}",peer);local_command(msg);}}
  if(node_id==0&&milliseconds>=3000&&milliseconds%300==0&&pid<60){char msg[64];printf("{\"event\":\"cooja_offer\",\"pid\":%u,\"now_ms\":%u}\n",pid,milliseconds);snprintf(msg,sizeof msg,"{\"originate\":1,\"pid\":%u}",pid++);local_command(msg);}
  for(unsigned i=0;i<48;i++)if(jobs[i].used&&!jobs[i].started&&(int32_t)(milliseconds-jobs[i].ready)>=0){linkaddr_t dest={{0}};dest.u8[0]=jobs[i].peer+1;packetbuf_clear();packetbuf_copyfrom(jobs[i].data,jobs[i].n);packetbuf_set_addr(PACKETBUF_ADDR_RECEIVER,&dest);packetbuf_set_addr(PACKETBUF_ADDR_SENDER,&linkaddr_node_addr);jobs[i].started=1;NETSTACK_MAC.send(tx_done,(void*)(uintptr_t)i);}
  if(milliseconds>=26500&&!done){done=1;energest_flush();printf("{\"event\":\"cooja_final\",\"node\":%u,\"offered\":%u,\"delivered\":%u,\"receipts\":%u,\"tx_queue_overflows\":%u,\"rx_queue_overflows\":%u,\"mac_attempts\":%u,\"mac_failures\":%u,\"raw_observations\":%u,\"cpu\":%llu,\"lpm\":%llu,\"tx\":%llu,\"listen\":%llu,\"hz\":%lu}\n",node_id,pid,delivered_count,receipt_count,queue_overflows,rx_queue_overflows,mac_attempts,mac_failures,raw_observations,(unsigned long long)energest_type_time(ENERGEST_TYPE_CPU),(unsigned long long)energest_type_time(ENERGEST_TYPE_LPM),(unsigned long long)energest_type_time(ENERGEST_TYPE_TRANSMIT),(unsigned long long)energest_type_time(ENERGEST_TYPE_LISTEN),(unsigned long)ENERGEST_SECOND);}
  etimer_set(&timer,CLOCK_SECOND/1000);
 }
 PROCESS_END();
}

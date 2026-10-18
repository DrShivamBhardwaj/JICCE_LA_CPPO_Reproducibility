/* Native Cooja transport diagnostic. PUBLIC TEST KEYS, not deployment firmware.
 * No attention policy or passive-credit semantics are claimed by this fixture. */
#include "contiki.h"
#include "net/netstack.h"
#include "net/nullnet/nullnet.h"
#include "sys/node-id.h"
#include "sys/energest.h"
#include "sha256.h"
#include "monocypher-ed25519.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
PROCESS(receipt_transport,"Authenticated receipt transport diagnostic");
AUTOSTART_PROCESSES(&receipt_transport);
static uint8_t tx[100],saved[100],sign_sk[64],sign_pk[32];
static uint32_t sequence,last_data,last_receipt,offered,delivered,receipts,rejected,replay_rejected,signature_rejected;
static unsigned injected_replay;
static void put32(uint8_t*p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static uint32_t get32(const uint8_t*p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static void hmac(const uint8_t*w,unsigned a,unsigned b,uint8_t*out){
 uint8_t key[64]={0},inner[32],outer[64];SHA256_CTX ctx;
 /* Deliberately public per-link fixture key; only virtual protocol checks. */
 for(int i=0;i<32;i++)key[i]=(uint8_t)(17*i+31*(a<b?a:b)+7*(a>b?a:b));
 for(int i=0;i<64;i++){outer[i]=key[i]^0x5c;key[i]^=0x36;}
 sha256_init(&ctx);sha256_update(&ctx,key,64);sha256_update(&ctx,w,20);sha256_update(&ctx,w+36,64);sha256_final(&ctx,inner);
 sha256_init(&ctx);sha256_update(&ctx,outer,64);sha256_update(&ctx,inner,32);sha256_final(&ctx,inner);memcpy(out,inner,16);
}
static int equal16(const uint8_t*a,const uint8_t*b){unsigned v=0;for(unsigned i=0;i<16;i++)v|=a[i]^b[i];return v==0;}
static void send_frame(uint8_t*w,unsigned next){
 linkaddr_t dest;memset(&dest,0,sizeof(dest));dest.u8[0]=next;
 w[1]=node_id;w[2]=next;hmac(w,node_id,next,w+20);
 nullnet_buf=w;nullnet_len=100;NETSTACK_NETWORK.output(&dest);
 printf("WIRE node=%u kind=%u seq=%lu next=%u hex=",node_id,w[0],(unsigned long)get32(w+4),next);
 for(unsigned i=0;i<100;i++)printf("%02x",w[i]);printf("\n");
}
static void receive(const void*data,uint16_t len,const linkaddr_t*src,const linkaddr_t*dest){
 uint8_t w[100],tag[16];uint32_t seq;(void)dest;
 if(len!=100)return;memcpy(w,data,100);seq=get32(w+4);
 hmac(w,w[1],node_id,tag);
 if(w[2]!=node_id||w[1]!=src->u8[0]||!equal16(tag,w+20)){rejected++;printf("REJECT node=%u type=hop seq=%lu\n",node_id,(unsigned long)seq);return;}
 if(w[0]==1){
  if(node_id==1||w[1]!=node_id-1)return;
  if(seq<=last_data){replay_rejected++;printf("REJECT node=%u type=replay seq=%lu\n",node_id,(unsigned long)seq);return;}last_data=seq;
  if(node_id<4){send_frame(w,node_id+1);return;}
  delivered++;printf("DELIVER node=4 seq=%lu\n",(unsigned long)seq);
  w[0]=3;crypto_ed25519_sign(w+36,sign_sk,w+4,16);send_frame(w,3);
 }else if(w[0]==3){
  if(node_id==4||w[1]!=node_id+1)return;
  if(crypto_ed25519_check(w+36,sign_pk,w+4,16)){signature_rejected++;printf("REJECT node=%u type=signature seq=%lu\n",node_id,(unsigned long)seq);return;}
  if(seq<=last_receipt){replay_rejected++;printf("REJECT node=%u type=receipt_replay seq=%lu\n",node_id,(unsigned long)seq);return;}last_receipt=seq;
  if(node_id>1){send_frame(w,node_id-1);return;}
  receipts++;printf("RECEIPT node=1 seq=%lu ticks=%lu hz=%lu\n",(unsigned long)seq,(unsigned long)(clock_time()-get32(w+8)),(unsigned long)CLOCK_SECOND);
 }
}
PROCESS_THREAD(receipt_transport,ev,data){
 static struct etimer timer;static unsigned phase;uint8_t seed[32];
 PROCESS_BEGIN();
 node_id=linkaddr_node_addr.u8[0];
 for(unsigned i=0;i<32;i++)seed[i]=(uint8_t)(i+1);crypto_ed25519_key_pair(sign_sk,sign_pk,seed);
 nullnet_set_input_callback(receive);etimer_set(&timer,5*CLOCK_SECOND);
 while(1){
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&timer));phase++;
  if(node_id==1&&phase<=103){
   if(phase==1){memset(tx,0,100);tx[0]=1;put32(tx+4,1);put32(tx+8,clock_time());tx[1]=1;tx[2]=2;hmac(tx,1,2,tx+20);tx[20]^=1;linkaddr_t dst={{2}};nullnet_buf=tx;nullnet_len=100;NETSTACK_NETWORK.output(&dst);printf("INJECT type=hop\n");}
   else if(sequence==50&&!injected_replay){memcpy(tx,saved,100);send_frame(tx,2);injected_replay=1;printf("INJECT type=replay\n");}
   else if(sequence<100){sequence++;offered++;memset(tx,0,100);tx[0]=1;put32(tx+4,sequence);put32(tx+8,clock_time());put32(tx+12,0x574e5331);send_frame(tx,2);memcpy(saved,tx,100);printf("OFFER seq=%lu ticks=%lu\n",(unsigned long)sequence,(unsigned long)clock_time());}
  }
  if(node_id==4&&phase==106){memset(tx,0,100);tx[0]=3;put32(tx+4,100);send_frame(tx,3);printf("INJECT type=signature\n");}
  if(phase==112){energest_flush();printf("FINAL node=%u offered=%lu delivered=%lu receipts=%lu bad_hop=%lu replay=%lu bad_signature=%lu cpu=%llu lpm=%llu tx=%llu listen=%llu energy_hz=%lu\n",node_id,(unsigned long)offered,(unsigned long)delivered,(unsigned long)receipts,(unsigned long)rejected,(unsigned long)replay_rejected,(unsigned long)signature_rejected,(unsigned long long)energest_type_time(ENERGEST_TYPE_CPU),(unsigned long long)energest_type_time(ENERGEST_TYPE_LPM),(unsigned long long)energest_type_time(ENERGEST_TYPE_TRANSMIT),(unsigned long long)energest_type_time(ENERGEST_TYPE_LISTEN),(unsigned long)ENERGEST_SECOND);}
  etimer_set(&timer,CLOCK_SECOND);
 }
 PROCESS_END();
}

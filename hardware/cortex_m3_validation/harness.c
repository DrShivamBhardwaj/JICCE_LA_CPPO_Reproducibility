/* Isolated Cortex-M3 actor and crypto harness. Test keys only, no radio stack. */
#include <stdint.h>
#include <stddef.h>
#include "vendor/sha256.h"
#include "vendor/monocypher-ed25519.h"
#include "generated/actor_vectors.h"
#ifdef MCU
static void emit(const char *s) {
 register unsigned r0 __asm__("r0")=4;
 register const char *r1 __asm__("r1")=s;
 __asm__ volatile("bkpt 0xab":"+r"(r0):"r"(r1):"memory");
}
static void finish(unsigned code) {
 unsigned args[2]={0x20026,code};
 register unsigned r0 __asm__("r0")=0x20;
 register unsigned *r1 __asm__("r1")=args;
 __asm__ volatile("bkpt 0xab":"+r"(r0):"r"(r1):"memory");
 for(;;){}
}
void *memcpy(void *d,const void *s,size_t n){unsigned char *a=d;const unsigned char*b=s;for(size_t i=0;i<n;i++)a[i]=b[i];return d;}
void *memset(void *d,int v,size_t n){unsigned char*a=d;for(size_t i=0;i<n;i++)a[i]=(unsigned char)v;return d;}
int memcmp(const void *a,const void*b,size_t n){const unsigned char*x=a,*y=b;for(size_t i=0;i<n;i++)if(x[i]!=y[i])return x[i]-y[i];return 0;}
#else
#include <stdio.h>
#include <string.h>
static void emit(const char*s){fputs(s,stdout);}
static void finish(unsigned code){(void)code;}
#endif
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
 for(int v=0;v<8;v++){
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
#ifdef MCU
extern uint32_t _bss_end,_stack_top;
#endif
int main(void){
 unsigned failures=0;
 for(unsigned n=0;n<16;n++){
  float logits[8];int action=actor(observations[n],masks[n],logits);
  emit("ACTOR ");hex32(n);hex32((uint32_t)action);
  for(int j=0;j<8;j++){union{float f;uint32_t u;}x;x.f=logits[j];hex32(x.u);}emit("\n");
 }
 unsigned char empty[8]={0};float scratch[8];
 if(actor(observations[0],empty,scratch)!=-1)failures++;
 uint8_t digest[32];hmac_sha256(digest);emit("HMAC ");hexbytes(digest,32);
 for(int i=0;i<32;i++)if(digest[i]!=hmac_expected[i])failures++;
 uint8_t seed[32],secret[64],public_key[32],signature[64];
 for(int i=0;i<32;i++)seed[i]=test_seed[i];
 crypto_ed25519_key_pair(secret,public_key,seed);
 crypto_ed25519_sign(signature,secret,test_message,sizeof test_message);
 int good=crypto_ed25519_check(test_signature,test_public,test_message,sizeof test_message);
 uint8_t corrupt[64];for(int i=0;i<64;i++)corrupt[i]=test_signature[i];corrupt[0]^=1;
 int bad=crypto_ed25519_check(corrupt,test_public,test_message,sizeof test_message);
 emit("ED25519 ");hex32((uint32_t)good);hex32((uint32_t)bad);emit("\nSIGNATURE ");hexbytes(signature,64);
 if(good!=0||bad==0)failures++;
 for(int i=0;i<64;i++)if(signature[i]!=test_signature[i])failures++;
#ifdef MCU
 volatile uint32_t *p=&_bss_end;while(p<&_stack_top&&*p==0xa5a5a5a5u)p++;
 emit("RAM ");hex32((uint32_t)&_bss_end-0x20000000u);hex32((uint32_t)&_stack_top-(uint32_t)p);emit("\n");
#endif
 emit("DONE ");hex32(failures);emit("\n");finish(failures);return (int)failures;
}
#ifdef MCU
extern uint32_t _data_start,_data_end,_data_load,_bss_start;
void Fault_Handler(void){emit("FAULT\n");finish(99);}
void Reset_Handler(void){
 uint32_t *s=&_data_load,*d=&_data_start;while(d<&_data_end)*d++=*s++;
 d=&_bss_start;while(d<&_bss_end)*d++=0;
 uint32_t sp;__asm__ volatile("mov %0, sp":"=r"(sp));
 for(d=&_bss_end;d<(uint32_t*)(sp-512);d++)*d=0xa5a5a5a5u;
 main();for(;;){}
}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[16]={
 (uintptr_t)&_stack_top,(uintptr_t)Reset_Handler,(uintptr_t)Fault_Handler,(uintptr_t)Fault_Handler,
 (uintptr_t)Fault_Handler,(uintptr_t)Fault_Handler,(uintptr_t)Fault_Handler,0,0,0,0,(uintptr_t)Fault_Handler,
 (uintptr_t)Fault_Handler,0,(uintptr_t)Fault_Handler,(uintptr_t)Fault_Handler};
#endif

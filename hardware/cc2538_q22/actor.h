/* Fixed-point approximation of the frozen FP32 actor. Bound checked at export. */
#include <stdint.h>
#include "q22_weights.h"
#define QS 22
#define QONE (1<<QS)
static int32_t qtanh(int32_t x){
 if(x<=-8*QONE)return -QONE;if(x>=8*QONE)return QONE;
 uint32_t u=(uint32_t)(x+8*QONE),index=u>>13,fraction=u&8191;
 return tanh_lut[index]+(int32_t)(((int64_t)(tanh_lut[index+1]-tanh_lut[index])*fraction+4096)>>13);
}
static void qlinear(const int32_t*x,int in,int out,const int32_t*w,const int32_t*b,int32_t*y,int activation){
 for(int j=0;j<out;j++){
  int64_t sum=b?(int64_t)b[j]*QONE:0;
  for(int i=0;i<in;i++)sum+=(int64_t)w[j*in+i]*x[i];
  int32_t z=(int32_t)((sum+(1<<(QS-1)))>>QS);y[j]=activation?qtanh(z):z;
 }
}
static int actor(const float*obs,const unsigned char*mask,float*logit){
 int32_t input[93],a[96],b[96],q[96],c[96],d[96],k[96],bias[48],value[1];
 for(int i=0;i<93;i++){if(!(obs[i]>=-32.f&&obs[i]<=32.f))return -1;input[i]=(int32_t)(obs[i]*QONE);}
 qlinear(input,13,96,q_ctx_encoder_0_weight,q_ctx_encoder_0_bias,a,1);
 qlinear(a,96,96,q_ctx_encoder_2_weight,q_ctx_encoder_2_bias,b,1);
 qlinear(b,96,96,q_query_weight,0,q,0);
 int best=-1;int64_t best_score=0;
 for(int v=0;v<8;v++){
  if(!mask[v]){logit[v]=-1.e9f;continue;}
  qlinear(input+13+10*v,10,96,q_cand_encoder_0_weight,q_cand_encoder_0_bias,c,1);
  qlinear(c,96,96,q_cand_encoder_2_weight,q_cand_encoder_2_bias,d,1);
  qlinear(d,96,96,q_key_weight,0,k,0);
  qlinear(d,96,48,q_actor_bias_0_weight,q_actor_bias_0_bias,bias,1);
  qlinear(bias,48,1,q_actor_bias_2_weight,q_actor_bias_2_bias,value,0);
  int64_t dot=0;for(int j=0;j<96;j++)dot+=(int64_t)q[j]*k[j];
  int64_t scaled=(dot+(1<<(QS-1)))>>QS;
  int64_t score=((scaled*428079+(1<<(QS-1)))>>QS)+value[0];
  logit[v]=(float)score/(float)QONE;
  if(best<0||score>best_score){best=v;best_score=score;}
 }
 return best;
}

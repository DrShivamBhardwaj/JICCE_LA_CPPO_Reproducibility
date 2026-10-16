/* CC2538 Renode register-level radio/UART bridge. Emulation target only.
 * Host performs routing and cryptography. No physical power claim.
 */
#include <stdint.h>
#define REG(a) (*(volatile uint32_t *)(a))
#define RF(o) REG(0x40088000u+(o))
#define UART_DR REG(0x4000c000u)
#define UART_FR REG(0x4000c018u)
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
static void ack(uint32_t token,int ok){text("{\"event\":\"ack\",\"token\":");number(token);text(ok?",\"ok\":true}\n":",\"ok\":false}\n");}
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
  }
 }
}
static void command(const char*s){
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
 REG(0x4000c02cu)=0x60u; /* UART 8-bit words */
 REG(0x4000c030u)=0x301u; /* UART enable, RX and TX */
 RF(0x5c8)=0x34;RF(0x5cc)=0x12;RF(0x5d0)=node_id+1u;RF(0x5d4)=0;
 RF(0x624)=0x60;RF(0x600)=0x0d;RF(0x604)=0x78;RF(0x608)=0;RF(0x63c)=11;
 RF(0x838)=0xed;RF(0x838)=0xee;RF(0x838)=0xe3;
 REG(0xe000e014u)=999;REG(0xe000e018u)=0;REG(0xe000e010u)=7;
 text("{\"event\":\"ready\",\"node\":");number(node_id);text("}\n");
 char line[768];unsigned used=0;int overflow=0;
 for(;;){
  radio_rx();
  for(unsigned i=0;i<256;i++)if(tokens[i]&&(int32_t)(milliseconds-expires[i])>=0){ack(tokens[i],0);tokens[i]=0;}
  if(!(UART_FR&16u)){
   char c=(char)UART_DR;
   if(c=='\n'){line[used]=0;if(!overflow)command(line);else text("{\"event\":\"error\",\"reason\":\"line_capacity\"}\n");used=0;overflow=0;}
   else if(c!='\r'){if(used+1<sizeof(line))line[used++]=c;else overflow=1;}
  }
 }
}

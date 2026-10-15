// ns-3.44 IEEE 802.15.4 packet bridge. No Python bindings required.
#include <ns3/core-module.h>
#include <ns3/network-module.h>
#include <ns3/mobility-module.h>
#include <ns3/lr-wpan-module.h>
#include <ns3/propagation-module.h>
#include <deque>
#include <map>
using namespace ns3;
using namespace ns3::lrwpan;
struct Event { double time; int kind,node,peer,pid,ok; };
static std::deque<Event> events;
static std::unique_ptr<LrWpanHelper> helper;
static NodeContainer nodes;
static NetDeviceContainer devices;
struct Pending {int peer,pid,previous,kind;};
static bool proofEnabled=true;
static double referenceLoss=40.;
struct Receiver {
 int id; uint8_t serial=0;
 double joules=0,last=0,txSeconds=0,rxSeconds=0,offSeconds=0; PhyEnumeration state=IEEE_802_15_4_PHY_TRX_OFF;
 int txFrames=0,txBytes=0,proofRequests=0,dataRequests=0;
 double current() { if(state==IEEE_802_15_4_PHY_BUSY_TX || state==IEEE_802_15_4_PHY_TX_ON) return .0174; if(state==IEEE_802_15_4_PHY_TRX_OFF) return .000020; return .0188; }
 void integrate() {double now=Simulator::Now().GetSeconds();double dt=now-last;double amps=current();joules+=dt*3.*amps;if(amps==.0174)txSeconds+=dt;else if(amps==.000020)offSeconds+=dt;else rxSeconds+=dt;last=now;}
 void change(Time,PhyEnumeration oldState,PhyEnumeration newState) {integrate();state=newState;}
 void tx(Ptr<const Packet> p) {txFrames++;txBytes+=p->GetSize();}
 std::map<int,Pending> pending;
 void send(int peer,int pid,int previous,int kind);
 void confirm(McpsDataConfirmParams p) {
  auto it=pending.find(p.m_msduHandle); if(it==pending.end()) return;
  auto x=it->second; pending.erase(it);
  bool ok=p.m_status==MacStatus::SUCCESS;
  events.push_back({Simulator::Now().GetSeconds(),3,id,x.peer,x.pid,ok});
  if(proofEnabled && ok && x.kind==0 && x.previous>=0) send(x.previous,x.pid,-1,1);
 }
 void receive(McpsDataIndicationParams p,Ptr<Packet> packet) {
  uint8_t buf[12]; if(packet->GetSize()<12) return; packet->CopyData(buf,12);
  int kind=buf[0],pid=buf[1]|(buf[2]<<8)|(buf[3]<<16),from=buf[4]|(buf[5]<<8);
  events.push_back({Simulator::Now().GetSeconds(),kind==0?1:(kind==1?2:(kind==2?5:6)),id,from,pid,static_cast<int>(p.m_mpduLinkQuality)});
 }
};
static std::vector<Receiver> receivers;
void Receiver::send(int peer,int pid,int previous,int kind) {
 uint8_t handle=serial++; if(pending.count(handle)) {events.push_back({Simulator::Now().GetSeconds(),4,id,peer,pid,0});return;}
 uint8_t buf[64]={}; buf[0]=kind;buf[1]=pid;buf[2]=pid>>8;buf[3]=pid>>16;buf[4]=id;buf[5]=id>>8;
 pending[handle]={peer,pid,previous,kind}; if(kind==0) dataRequests++; else if(kind==1) proofRequests++;
 McpsDataRequestParams p; p.m_srcAddrMode=SHORT_ADDR;p.m_dstAddrMode=SHORT_ADDR;p.m_dstPanId=1;
 p.m_dstAddr=Mac16Address(peer+1);p.m_msduHandle=handle;p.m_txOptions=kind==2?0:TX_OPTION_ACK;
 Simulator::ScheduleWithContext(id,Seconds(0),&LrWpanMac::McpsDataRequest,DynamicCast<LrWpanNetDevice>(devices.Get(id))->GetMac(),p,Create<Packet>(buf,64));
}
extern "C" {
void bridge_init(int count,const double* xy,int seed,double range) {
 Simulator::Destroy();events.clear(); receivers.clear();devices=NetDeviceContainer();nodes=NodeContainer();
 RngSeedManager::SetSeed(seed);RngSeedManager::SetRun(1);nodes.Create(count);
 MobilityHelper m;m.SetMobilityModel("ns3::ConstantPositionMobilityModel");m.Install(nodes);
 for(int i=0;i<count;i++) nodes.Get(i)->GetObject<MobilityModel>()->SetPosition(Vector(xy[2*i],xy[2*i+1],0));
 helper=std::make_unique<LrWpanHelper>(); auto& h=*helper; h.AddPropagationLossModel("ns3::LogDistancePropagationLossModel","Exponent",DoubleValue(3.0),"ReferenceLoss",DoubleValue(referenceLoss)); h.AddPropagationLossModel("ns3::RangePropagationLossModel","MaxRange",DoubleValue(range));
 devices=h.Install(nodes);h.AssignStreams(devices,10);
 receivers.resize(count);
 for(int i=0;i<count;i++) {auto mac=DynamicCast<LrWpanNetDevice>(devices.Get(i))->GetMac(); DynamicCast<LrWpanNetDevice>(devices.Get(i))->GetPhy()->SetMobility(nodes.Get(i)->GetObject<MobilityModel>()); receivers[i].id=i;DynamicCast<LrWpanNetDevice>(devices.Get(i))->SetAddress(Mac16Address(i+1));mac->SetPanId(1);auto phy=DynamicCast<LrWpanNetDevice>(devices.Get(i))->GetPhy();phy->TraceConnectWithoutContext("TrxState",MakeCallback(&Receiver::change,&receivers[i]));phy->TraceConnectWithoutContext("PhyTxBegin",MakeCallback(&Receiver::tx,&receivers[i]));mac->SetMcpsDataConfirmCallback(MakeCallback(&Receiver::confirm,&receivers[i]));mac->SetMcpsDataIndicationCallback(MakeCallback(&Receiver::receive,&receivers[i]));}
}
void bridge_send(int node,int peer,int pid,int previous) {receivers.at(node).send(peer,pid,previous,0);}
void bridge_step(double seconds) {Simulator::Stop(Seconds(seconds));Simulator::Run();}
int bridge_poll(Event* out) {if(events.empty()) return 0;*out=events.front();events.pop_front();return 1;}
void bridge_receipt(int node,int peer,int pid) {receivers.at(node).send(peer,pid,-1,3);}
void bridge_beacon(int node,int sequence) {receivers.at(node).send(-2,sequence,-1,2);}
void bridge_options(int proofs,double refLoss) {proofEnabled=proofs;referenceLoss=refLoss;}
void bridge_telemetry(int node,double* out) {auto& r=receivers.at(node);r.integrate();out[0]=r.joules;out[1]=r.pending.size();out[2]=r.txFrames;out[3]=r.txBytes;out[4]=r.proofRequests;out[5]=r.dataRequests;out[6]=r.txSeconds;out[7]=r.rxSeconds;out[8]=r.offSeconds;}
void bridge_destroy() {Simulator::Destroy();}
}

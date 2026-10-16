// Variable-length wire transport for the separate authenticated prototype.
#include <ns3/core-module.h>
#include <ns3/network-module.h>
#include <ns3/mobility-module.h>
#include <ns3/lr-wpan-module.h>
#include <ns3/propagation-module.h>
#include <deque>
#include <map>
#include <array>
#include <cstring>
using namespace ns3;using namespace ns3::lrwpan;
struct WireEvent{double time;int kind,node,peer,handle,ok,length;uint8_t bytes[114];};
static std::deque<WireEvent> events;static NodeContainer nodes;static NetDeviceContainer devices;static std::unique_ptr<LrWpanHelper> helper;
struct Receiver{
 int id=0,serial=0,frames=0,bytes=0;double last=0,joules=0,txTime=0,rxTime=0,offTime=0;PhyEnumeration state=IEEE_802_15_4_PHY_TRX_OFF;
 std::map<int,int> pending;
 void integrate(){double now=Simulator::Now().GetSeconds(),dt=now-last;double a=(state==IEEE_802_15_4_PHY_BUSY_TX||state==IEEE_802_15_4_PHY_TX_ON)?.0174:(state==IEEE_802_15_4_PHY_TRX_OFF?.000020:.0188);joules+=3*a*dt;if(a==.0174)txTime+=dt;else if(a==.000020)offTime+=dt;else rxTime+=dt;last=now;}
 void change(Time,PhyEnumeration,PhyEnumeration next){integrate();state=next;}
 void tx(Ptr<const Packet> p){frames++;bytes+=p->GetSize();}
 void confirm(McpsDataConfirmParams p){auto it=pending.find(p.m_msduHandle);if(it==pending.end())return;WireEvent e{};e.time=Simulator::Now().GetSeconds();e.kind=2;e.node=id;e.peer=it->second;e.handle=p.m_msduHandle;e.ok=p.m_status==MacStatus::SUCCESS;pending.erase(it);events.push_back(e);}
 void receive(McpsDataIndicationParams p,Ptr<Packet> packet){if(packet->GetSize()>114)return;WireEvent e{};e.time=Simulator::Now().GetSeconds();e.kind=1;e.node=id;uint8_t addr[2];p.m_srcAddr.CopyTo(addr);e.peer=((int)addr[0]*256+addr[1])-1;e.length=packet->GetSize();e.ok=p.m_mpduLinkQuality;packet->CopyData(e.bytes,e.length);events.push_back(e);}
};
static std::vector<Receiver> receivers;
extern "C"{
void wire_init(int n,const double* xy,int seed,double range){Simulator::Destroy();events.clear();receivers.clear();nodes=NodeContainer();devices=NetDeviceContainer();RngSeedManager::SetSeed(seed);RngSeedManager::SetRun(1);nodes.Create(n);MobilityHelper m;m.SetMobilityModel("ns3::ConstantPositionMobilityModel");m.Install(nodes);for(int i=0;i<n;i++)nodes.Get(i)->GetObject<MobilityModel>()->SetPosition(Vector(xy[2*i],xy[2*i+1],0));helper=std::make_unique<LrWpanHelper>();helper->AddPropagationLossModel("ns3::LogDistancePropagationLossModel","Exponent",DoubleValue(3.),"ReferenceLoss",DoubleValue(40.));helper->AddPropagationLossModel("ns3::RangePropagationLossModel","MaxRange",DoubleValue(range));devices=helper->Install(nodes);helper->AssignStreams(devices,10);receivers.resize(n);for(int i=0;i<n;i++){auto dev=DynamicCast<LrWpanNetDevice>(devices.Get(i));dev->SetAddress(Mac16Address(i+1));auto mac=dev->GetMac();mac->SetPanId(1);auto phy=dev->GetPhy();phy->SetMobility(nodes.Get(i)->GetObject<MobilityModel>());receivers[i].id=i;phy->TraceConnectWithoutContext("TrxState",MakeCallback(&Receiver::change,&receivers[i]));phy->TraceConnectWithoutContext("PhyTxBegin",MakeCallback(&Receiver::tx,&receivers[i]));mac->SetMcpsDataConfirmCallback(MakeCallback(&Receiver::confirm,&receivers[i]));mac->SetMcpsDataIndicationCallback(MakeCallback(&Receiver::receive,&receivers[i]));}}
int wire_send(int node,int peer,const uint8_t* bytes,int length){if(node<0||peer<0||node>=(int)receivers.size()||peer>=(int)receivers.size()||length<1||length>114)return -1;auto&r=receivers[node];int handle=-1;for(int i=0;i<256;i++){int candidate=r.serial++%256;if(!r.pending.count(candidate)){handle=candidate;break;}}if(handle<0)return -1;r.pending[handle]=peer;McpsDataRequestParams p;p.m_srcAddrMode=SHORT_ADDR;p.m_dstAddrMode=SHORT_ADDR;p.m_dstPanId=1;p.m_dstAddr=Mac16Address(peer+1);p.m_msduHandle=handle;p.m_txOptions=TX_OPTION_ACK;Simulator::ScheduleWithContext(node,Seconds(0),&LrWpanMac::McpsDataRequest,DynamicCast<LrWpanNetDevice>(devices.Get(node))->GetMac(),p,Create<Packet>(bytes,length));return handle;}
void wire_step(double seconds){Simulator::Stop(Seconds(seconds));Simulator::Run();}
int wire_poll(WireEvent*out){if(events.empty())return 0;*out=events.front();events.pop_front();return 1;}
void wire_energy(int node,double*out){auto&r=receivers.at(node);r.integrate();out[0]=r.joules;out[1]=r.txTime;out[2]=r.rxTime;out[3]=r.offTime;out[4]=r.frames;out[5]=r.bytes;out[6]=r.pending.size();}
void wire_destroy(){Simulator::Destroy();}
}

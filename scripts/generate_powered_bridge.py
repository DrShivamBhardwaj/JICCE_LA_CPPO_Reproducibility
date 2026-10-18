"""Generate a separate power-gated bridge without modifying frozen sources."""
from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/"src/ns3_bridge/passive_bridge.cc").read_text()
s=s.replace("#include <map>","#include <map>\n#include <cmath>\n#include <limits>\n#include <ns3/spectrum-channel.h>")
s=s.replace(" int id; uint8_t serial=0;",""" int id; uint8_t serial=0;
 bool powered=true;
 double budget=std::numeric_limits<double>::infinity(), depletedAt=-1.;
 int rejectedSends=0,postCutTx=0;
 EventId energyEvent;
 void armEnergy();
 void cutPower();
""")
s=s.replace("void integrate() {double now=Simulator::Now().GetSeconds();double dt=now-last;double amps=current();joules+=dt*3.*amps;", "void integrate() {double now=Simulator::Now().GetSeconds();double dt=now-last;if(!powered){last=now;return;}double amps=current();if(std::isfinite(budget))dt=std::min(dt,std::max(0.,budget-joules)/(3.*amps));joules+=dt*3.*amps;")
s=s.replace("integrate();state=newState;}", "integrate();state=newState;armEnergy();}")
s=s.replace("void tx(Ptr<const Packet> p) {txFrames++;", "void tx(Ptr<const Packet> p) {if(!powered){postCutTx++;return;}txFrames++;")
s=s.replace("  auto it=pending.find", "  if(!powered)return;\n  auto it=pending.find")
s=s.replace(" void overhear(Ptr<const Packet> frame) {", " void overhear(Ptr<const Packet> frame) {\n  if(!powered)return;")
s=s.replace(" void receive(McpsDataIndicationParams p,Ptr<Packet> packet) {", " void receive(McpsDataIndicationParams p,Ptr<Packet> packet) {\n  if(!powered)return;")
s=s.replace("void Receiver::send(int peer,int pid,int previous,int kind) {", "void Receiver::send(int peer,int pid,int previous,int kind) {\n if(!powered){rejectedSends++;return;}")
anchor='extern "C" {'
methods="""void Receiver::armEnergy() {
 energyEvent.Cancel();
 if(!powered || !std::isfinite(budget))return;
 double seconds=std::max(0.,budget-joules)/(3.*current());
 energyEvent=Simulator::Schedule(Seconds(std::max(1e-9,seconds)),&Receiver::cutPower,this);
}
void Receiver::cutPower() {
 integrate();
 if(joules+1e-10<budget){armEnergy();return;}
 powered=false;depletedAt=Simulator::Now().GetSeconds();energyEvent.Cancel();
 auto device=DynamicCast<LrWpanNetDevice>(devices.Get(id));
 helper->GetChannel()->RemoveRx(device->GetPhy());
 auto phy=device->GetPhy();
 phy->SetPdDataConfirmCallback(MakeNullCallback<void,PhyEnumeration>());
 phy->SetPlmeSetTRXStateConfirmCallback(MakeNullCallback<void,PhyEnumeration>());
 phy->SetPlmeCcaConfirmCallback(MakeNullCallback<void,PhyEnumeration>());
 phy->SetPlmeEdConfirmCallback(MakeNullCallback<void,PhyEnumeration,uint8_t>());
 // Retain live MAC objects; suppress PHY confirmations after power loss.
 device->GetPhy()->PlmeSetTRXStateRequest(IEEE_802_15_4_PHY_FORCE_TRX_OFF);
 pending.clear();
 events.push_back({depletedAt,8,id,-1,-1,1});
}
"""
s=s.replace(anchor,methods+anchor)
s=s.replace("void bridge_send(int node", """void bridge_power_budget(int node,double joules) {
 NS_ABORT_MSG_IF(!std::isfinite(joules)||joules<0,"Invalid power budget");
 auto& r=receivers.at(node);r.integrate();
 NS_ABORT_MSG_IF(joules<r.joules,"Budget below energy already consumed");
 r.budget=joules;r.armEnergy();
}
void bridge_power_status(int node,double* out) {
 auto& r=receivers.at(node);r.integrate();
 out[0]=r.powered;out[1]=r.budget;out[2]=r.depletedAt;
 out[3]=r.rejectedSends;out[4]=r.postCutTx;
}
void bridge_send(int node""")
(r/"src/ns3_bridge/powered_bridge.cc").write_text(s)
print("Generated separate power-gated bridge")

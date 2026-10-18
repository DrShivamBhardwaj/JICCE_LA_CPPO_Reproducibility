"""Add periodic PHY sleep/wake primitives to the generated experimental bridge."""
from pathlib import Path
r=Path(__file__).resolve().parents[1];p=r/"src/ns3_bridge/powered_bridge.cc";s=p.read_text()
s=s.replace(" bool powered=true;", """ bool powered=true,awake=true,sleepRequested=false;
 MacState macState=MAC_IDLE;
 void macChange(MacState,MacState next){macState=next;}
 int sleepingRejected=0,sleepDeferrals=0;
 EventId sleepEvent;
 void trySleep();
 void setAwake(bool on);
""")
s=s.replace("if(!powered){rejectedSends++;return;}","if(!powered){rejectedSends++;return;}\n if(!awake){sleepingRejected++;return;}")
anchor="void Receiver::armEnergy()"
methods="""void Receiver::trySleep() {
 if(!powered || !sleepRequested)return;
 if(macState!=MAC_IDLE || !pending.empty() || state==IEEE_802_15_4_PHY_BUSY_TX || state==IEEE_802_15_4_PHY_BUSY_RX) {
  sleepDeferrals++;sleepEvent=Simulator::Schedule(MilliSeconds(1),&Receiver::trySleep,this);return;
 }
 integrate();awake=false;
 auto d=DynamicCast<LrWpanNetDevice>(devices.Get(id));
 d->GetMac()->SetRxOnWhenIdle(false);
 d->GetPhy()->PlmeSetTRXStateRequest(IEEE_802_15_4_PHY_TRX_OFF);
}
void Receiver::setAwake(bool on) {
 sleepEvent.Cancel();sleepRequested=!on;
 if(!powered)return;
 if(!on){if(awake)trySleep();return;}
 if(awake)return;
 integrate();awake=true;
 auto d=DynamicCast<LrWpanNetDevice>(devices.Get(id));
 d->GetMac()->SetRxOnWhenIdle(true);
 d->GetPhy()->PlmeSetTRXStateRequest(IEEE_802_15_4_PHY_RX_ON);
}
"""
s=s.replace(anchor,methods+anchor)
s=s.replace('mac->SetPanId(1);','mac->SetPanId(1);mac->TraceConnectWithoutContext("MacStateValue",MakeCallback(&Receiver::macChange,&receivers[i]));')
s=s.replace("powered=false;depletedAt=","powered=false;sleepEvent.Cancel();depletedAt=")
s=s.replace('void bridge_power_budget(int node',"""void bridge_awake(int node,int on) {receivers.at(node).setAwake(on!=0);}
void bridge_duty_status(int node,double* out) {
 auto& r=receivers.at(node);out[0]=r.awake;out[1]=r.sleepingRejected;out[2]=r.sleepDeferrals;
}
void bridge_power_budget(int node""")
p.write_text(s)

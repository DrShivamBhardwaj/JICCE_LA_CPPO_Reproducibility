<?xml version='1.0' encoding='UTF-8'?>
<simconf version="2022112801">
  <simulation>
    <title>Separate frozen policy and weighted feedback port</title>
    <randomseed>93007</randomseed>
    <motedelay_us>0</motedelay_us>
    <radiomedium>
      org.contikios.cooja.radiomediums.UDGM
      <transmitting_range>50.0</transmitting_range>
      <interference_range>100.0</interference_range>
      <success_ratio_tx>1.0</success_ratio_tx>
      <success_ratio_rx>1.0</success_ratio_rx>
    </radiomedium>
    <events>
      <logoutput>40000</logoutput>
    </events>
    <motetype>
      org.contikios.cooja.contikimote.ContikiMoteType
      <description>Native Cooja; not Cortex-M3 cycle emulation</description>
      <source>/Users/shivambhardwaj/Research/WSN_Array_Validation_20261018/build/cooja_feedback_workers/worker1/feedback.c</source>
      <commands>make feedback.cooja TARGET=cooja CONTIKI=/Users/shivambhardwaj/Research/WSN_Array_Validation_20261018/build/contiki-feedback</commands>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Battery</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiVib</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRS232</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiBeeper</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.RimeAddress</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.IPAddress</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiRadio</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiButton</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiPIR</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiClock</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiLED</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiCFS</moteinterface>
      <moteinterface>org.contikios.cooja.contikimote.interfaces.ContikiEEPROM</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Mote2MoteRelations</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.MoteAttributes</moteinterface>
      <mote><interface_config>org.contikios.cooja.interfaces.Position<pos x="0" y="0" /></interface_config><interface_config>org.contikios.cooja.contikimote.interfaces.ContikiMoteID<id>1</id></interface_config></mote><mote><interface_config>org.contikios.cooja.interfaces.Position<pos x="45" y="15" /></interface_config><interface_config>org.contikios.cooja.contikimote.interfaces.ContikiMoteID<id>2</id></interface_config></mote><mote><interface_config>org.contikios.cooja.interfaces.Position<pos x="45" y="-15" /></interface_config><interface_config>org.contikios.cooja.contikimote.interfaces.ContikiMoteID<id>3</id></interface_config></mote><mote><interface_config>org.contikios.cooja.interfaces.Position<pos x="90" y="0" /></interface_config><interface_config>org.contikios.cooja.contikimote.interfaces.ContikiMoteID<id>4</id></interface_config></mote></motetype>
  </simulation>
  <plugin>org.contikios.cooja.plugins.ScriptRunner<plugin_config><script>TIMEOUT(30000, log.testFailed());
var Serial=Java.type("org.contikios.cooja.contikimote.interfaces.ContikiRS232");
var finals={};var sent={};
while(Object.keys(finals).length&lt;4){
 YIELD();log.log(time+" node-"+id+" "+msg+"\n");
 if(msg.indexOf("Link-layer address:")&gt;=0&amp;&amp;!sent[id]){mote.getInterfaces().getInterfaceOfType(Serial.class).writeString("CONFIG 0 0 0 0");sent[id]=true;}
 if(msg.startsWith("{\"event\":\"cooja_final\"")){var x=JSON.parse(msg);if(x.node!==id-1)log.testFailed();finals[id]=true;}
}
log.testOK();</script><active>true</active></plugin_config></plugin></simconf>
"""Read-only presence check; never a physical measurement certificate."""
import json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
from serial.tools import list_ports
r=Path(__file__).resolve().parents[1]
ports=[dict(port=p.device,description=p.description) for p in list_ports.comports() if p.vid is not None]
try:tree=json.loads(subprocess.check_output(['system_profiler','SPUSBDataType','-json'],text=True,timeout=30))
except (subprocess.SubprocessError,json.JSONDecodeError):tree={}
matching=[]
def visit(x):
 if isinstance(x,dict):
  name=x.get('_name','')
  if re.search(r'CC2538|J-Link|CMSIS|Joulescope|Power Profiler|SEGGER|Texas Instruments',name,re.I):matching.append(name)
  for value in x.values():visit(value)
 elif isinstance(x,list):
  for value in x:visit(value)
visit(tree)
report=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),usb_serial_interfaces=ports,matching_board_or_instrument_names=matching,physical_measurements_acquired=False,physical_validation=False,scope='Attached USB presence only; does not discover off-device hardware or establish instrument calibration. No serial numbers retained.')
p=r/'outputs/cc2538_fast/hardware_presence.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

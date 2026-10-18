"""Build power-state regression bridge against ns3 3.44.post0; not a rerun of the historical ns3 3.47 factorial study."""
from pathlib import Path
import importlib.metadata
import subprocess
ROOT=Path(__file__).resolve().parents[1]
ns=Path(importlib.metadata.distribution('ns3').locate_file('ns3'))
out=ROOT/'build/libwsn_ns3_powered.so';out.parent.mkdir(exist_ok=True)
subprocess.run(['g++','-std=c++20','-O2','-shared','-fPIC',str(ROOT/'src/ns3_bridge/powered_bridge.cc'),'-I'+str(ns/'include'),'-L'+str(ns/'lib64'),'-Wl,-rpath,'+str(ns/'lib64'),'-o',str(out)]+['-lns3.44-'+m for m in ['lr-wpan','spectrum','propagation','mobility','network','core']],check=True)
print(out)

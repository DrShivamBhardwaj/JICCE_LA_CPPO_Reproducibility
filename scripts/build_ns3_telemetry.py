"""Build against the ns3==3.44.post0 wheel without importing cppyy."""
from pathlib import Path
import importlib.metadata
import subprocess
ROOT=Path(__file__).resolve().parents[1]
ns=Path(importlib.metadata.distribution('ns3').locate_file('ns3'))
out=ROOT/'build/libwsn_ns3_telemetry.so';out.parent.mkdir(exist_ok=True)
subprocess.run(['g++','-std=c++20','-O2','-shared','-fPIC',str(ROOT/'src/ns3_bridge/telemetry_bridge.cc'),'-I'+str(ns/'include'),'-L'+str(ns/'lib64'),'-Wl,-rpath,'+str(ns/'lib64'),'-o',str(out)]+['-lns3.44-'+m for m in ['lr-wpan','spectrum','propagation','mobility','network','core']],check=True)
print(out)

"""Build a separate portability-check backend against an explicit ns-3 prefix."""
import argparse, json, subprocess, platform
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--prefix",type=Path,required=True);p.add_argument("--version",required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/"build";out.mkdir(exist_ok=True)
libs=a.prefix/"lib";include=a.prefix/"include";commands=[]
for name,src in [("","bridge"),("_telemetry","telemetry_bridge"),("_passive","passive_bridge"),("_wire","wire_bridge")]:
    cmd=["c++","-std=c++20","-O2","-shared","-fPIC",str(root/"src/ns3_bridge"/(src+".cc")),"-I"+str(include),"-L"+str(libs),"-Wl,-rpath,"+str(libs),"-o",str(out/("libwsn_ns3"+name+".so"))]+["-lns"+a.version+"-"+m+"-optimized" for m in ["lr-wpan","spectrum","propagation","mobility","network","core"]]
    subprocess.run(cmd,check=True);commands.append(cmd)
dest=root/"outputs/validation_20261018";dest.mkdir(parents=True,exist_ok=True)
(dest/"backend_build.json").write_text(json.dumps(dict(ns3_version=a.version,platform=platform.platform(),commands=commands,scope="Portability check; not a reproduction of the ns-3.44 frozen evidence"),indent=2)+"\n")

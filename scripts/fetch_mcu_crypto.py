"""Fetch pinned public crypto sources for the isolated MCU validation harness."""
from pathlib import Path
import urllib.request,hashlib,tarfile,io,json
r=Path(__file__).resolve().parents[1];out=r/"hardware/cortex_m3_validation/vendor";out.mkdir(parents=True,exist_ok=True)
url="https://github.com/LoupVaillant/Monocypher/releases/download/4.0.3/monocypher-4.0.3.tar.gz"
blob=urllib.request.urlopen(url,timeout=60).read()
assert hashlib.sha256(blob).hexdigest()=="8cc9bc341a66249016db9bd70e9142d8d0aef9945973744b1ac05dbc55d8ee66"
sources={}
with tarfile.open(fileobj=io.BytesIO(blob),mode="r:gz") as tar:
 for name in ["src/monocypher.c","src/monocypher.h","src/optional/monocypher-ed25519.c","src/optional/monocypher-ed25519.h","LICENCE.md"]:
  member=next(m for m in tar.getmembers() if m.name.endswith("/"+name))
  b=tar.extractfile(member).read();dest=out/Path(name).name;dest.write_bytes(b);sources[dest.name]=dict(url=url,sha256=hashlib.sha256(b).hexdigest())
pin="cfbde48414baacf51fc7c74f275190881f037d32"
for name in ["sha256.c","sha256.h","README.md"]:
 u="https://raw.githubusercontent.com/B-Con/crypto-algorithms/"+pin+"/"+name;b=urllib.request.urlopen(u,timeout=30).read()
 dest=out/("BCon_README.md" if name=="README.md" else name);dest.write_bytes(b);sources[dest.name]=dict(url=u,sha256=hashlib.sha256(b).hexdigest())
(out/"provenance.json").write_text(json.dumps(sources,indent=2)+"\n")
print("Pinned crypto sources downloaded and hashed")

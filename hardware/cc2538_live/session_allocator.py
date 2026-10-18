"""Host-side persistent emulator boot-session allocation, not MCU NVM support."""
from pathlib import Path
import os,json,fcntl,secrets

def allocate(path,count=4):
 if count<1:raise ValueError('positive count required')
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(path,os.O_RDWR|os.O_CREAT,0o600)
 with os.fdopen(fd,'r+') as f:
  fcntl.flock(f,fcntl.LOCK_EX);raw=f.read();start=json.loads(raw)['next'] if raw else secrets.randbits(48)+1
  if not isinstance(start,int) or not 0<start<2**64-count:raise ValueError('session allocator exhausted/corrupt')
  end=start+count;f.seek(0);f.write(json.dumps(dict(next=end)));f.truncate();f.flush();os.fsync(f.fileno())
 return list(range(start,end))

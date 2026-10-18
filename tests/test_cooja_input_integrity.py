import gzip
import hashlib
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('integrity',Path(__file__).resolve().parents[1]/'scripts/cooja_input_integrity.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
@pytest.fixture
def archive(tmp_path):
    raw=b'Random seed: 93001\nTEST OK\n';image=b'native image fixture'
    (tmp_path/'COOJA.testlog.gz').write_bytes(gzip.compress(raw,mtime=0))
    (tmp_path/'native_mote.dylib').write_bytes(image)
    return tmp_path,{'log_sha256':hashlib.sha256(raw).hexdigest()},{'native_image_sha256':hashlib.sha256(image).hexdigest(),'returncode':0},raw

def test_intact_compressed_archive(archive):
    folder,audit,run,raw=archive
    assert m.verify_run_inputs(folder,audit,run)==raw

@pytest.mark.parametrize('change',['log','image','conflicting_copy','failed_runner'])
def test_changed_inputs_rejected(archive,change):
    folder,audit,run,raw=archive
    if change=='log':(folder/'COOJA.testlog.gz').write_bytes(gzip.compress(raw+b'changed'))
    elif change=='image':(folder/'native_mote.dylib').write_bytes(b'changed')
    elif change=='conflicting_copy':(folder/'COOJA.testlog').write_bytes(raw+b'changed')
    else:run['returncode']=1
    with pytest.raises(ValueError):m.verify_run_inputs(folder,audit,run)

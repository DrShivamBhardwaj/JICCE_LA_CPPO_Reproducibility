"""Reject stale analysis captures; hashes do not authenticate coordinated edits."""
import gzip
import hashlib
from pathlib import Path


def verify_run_inputs(folder, audit, run):
    folder = Path(folder)
    raw_path, packed_path = folder/'COOJA.testlog', folder/'COOJA.testlog.gz'
    raw = raw_path.read_bytes() if raw_path.exists() else gzip.decompress(packed_path.read_bytes())
    if raw_path.exists() and packed_path.exists() and raw != gzip.decompress(packed_path.read_bytes()):
        raise ValueError(f'Conflicting raw/compressed logs: {folder}')
    if hashlib.sha256(raw).hexdigest() != audit['log_sha256']:
        raise ValueError(f'Stale audit: log hash mismatch: {folder}')
    if hashlib.sha256((folder/'native_mote.dylib').read_bytes()).hexdigest() != run['native_image_sha256']:
        raise ValueError(f'Native image hash mismatch: {folder}')
    if run['returncode'] != 0:
        raise ValueError(f'Runner did not complete successfully: {folder}')
    return raw

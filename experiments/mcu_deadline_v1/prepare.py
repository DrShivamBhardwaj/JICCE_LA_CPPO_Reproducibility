"""Compiler-only O3 pilot: unchanged Q22 actor, crypto, receipt endpoint and clocks."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;B=R/'build/mcu_deadline_v1'

def main():
    protocol=json.loads((D/'protocol.json').read_text())
    for name,sha in protocol['source_sha256'].items():
        if hashlib.sha256((R/name).read_bytes()).hexdigest()!=sha:raise ValueError('Frozen MCU source changed: '+name)
    B.mkdir(parents=True,exist_ok=True)
    for original,target in [('build_cc2538_q22.py','build_generated.py'),('run_cc2538_q22.py','run_generated.py'),('audit_cc2538_q22.py','audit_generated.py')]:
        text=(R/'scripts'/original).read_text().replace('Path(__file__).resolve().parents[1]','Path(__file__).resolve().parents[2]').replace('outputs/cc2538_q22','outputs/mcu_deadline_v1').replace('from audit_cc2538_q22 import audit_run','from audit_generated import audit_run')
        if original.startswith('build_'):
            if "'-O2'" not in text:raise ValueError('optimization anchor')
            text=text.replace("'-O2'","'-O3'")
        if original.startswith('run_'):
            text=text.replace("private_root=Path.home()/'Research/wsn-private-validation'","private_root=Path(os.environ['WSN_PRIVATE_ROOT'])")
        (B/target).write_text(text)
if __name__=='__main__':main()

"""Packet attribution must fail closed when stage provenance is ambiguous."""
import importlib.util,json,tempfile,unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('signed_path',Path(__file__).resolve().parents[1]/'scripts/diagnose_signed_critical_path.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class SignedPathAttributionTests(unittest.TestCase):
    def test_reject_unsupported_stage_attribution(self):
        fixtures=[
            [{'event':'local_receipt','pid':1}],
            [{'event':'stage_time','stage':'verify','elapsed_ms':82},{'event':'reject'},{'event':'local_receipt','pid':1}],
            [{'event':'stage_time','stage':'sign','elapsed_ms':30},{'event':'local_receipt','pid':1}],
            [{'event':'stage_time','stage':'verify','elapsed_ms':82},{'event':'local_receipt','pid':1}]*2,
        ]
        with tempfile.TemporaryDirectory() as directory:
            capture=Path(directory)/'uart.jsonl'
            for records in fixtures:
                with self.subTest(records=records):
                    capture.write_text(''.join(json.dumps(r)+'\n' for r in records))
                    with self.assertRaises(ValueError):module.stage_by_packet(capture,'verify','local_receipt')

    def test_adjacent_authenticated_receipt_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            capture=Path(directory)/'uart.jsonl'
            capture.write_text('{"event":"stage_time","stage":"verify","elapsed_ms":82}\n{"event":"local_receipt","pid":1}\n')
            self.assertEqual(module.stage_by_packet(capture,'verify','local_receipt'),{1:82})

if __name__=='__main__':unittest.main()

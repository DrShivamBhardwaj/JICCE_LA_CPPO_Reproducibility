"""Exploratory per-packet accounting of retained emulator stages, never physical timing.

Stage events have no packet IDs: only immediate adjacency to an authenticated
receipt/delivery event is accepted. A missing adjacency fails rather than guessing.
"""
import argparse, hashlib, json, statistics
from pathlib import Path


def stage_by_packet(path, stage, event):
    records = [json.loads(line) for line in path.read_text().splitlines()]
    result = {}
    for index, row in enumerate(records):
        if row.get('event') != event:
            continue
        if index == 0:
            raise ValueError('Missing preceding stage')
        previous = records[index - 1]
        if previous.get('event') != 'stage_time' or previous.get('stage') != stage:
            raise ValueError('Stage cannot be attributed by immediate adjacency')
        pid = row['pid']
        if pid in result:
            raise ValueError('Duplicate packet stage')
        result[pid] = previous['elapsed_ms']
    return result


def diagnose(folder):
    verification = json.loads((folder / 'verification.json').read_text())
    if verification['status'] != 'passed':
        raise ValueError('Functional acceptance absent')
    sign = stage_by_packet(folder / 'uart_3.jsonl', 'sign', 'local_sink_delivery')
    verify = stage_by_packet(folder / 'uart_0.jsonl', 'verify', 'local_receipt')
    delays = verification['emulated_receipt_delays']
    # The archived acceptance convention is strictly greater than the deadline.
    ids = {row['pid'] for row in delays}
    if len(ids) != 100 or len(delays) != 100 or ids != set(sign) or ids != set(verify):
        raise ValueError('Incomplete or duplicate matched packet coverage')
    packets = []
    for row in delays:
        pid = row['pid']
        crypto = sign[pid] + verify[pid]
        delay = row['receipt_delay_ms']
        if crypto > delay:
            raise ValueError('Accounted serial stages exceed source delay')
        limit = [90, 350, 1500][row['traffic']]
        packets.append(dict(pid=pid, traffic=row['traffic'], deadline_ms=limit,
                            receipt_ms=delay, sink_sign_ms=sign[pid],
                            source_verify_ms=verify[pid], endpoint_crypto_ms=crypto,
                            remaining_serial_path_ms=delay-crypto,
                            deadline_miss=delay > limit, endpoint_crypto_exceeds_deadline=crypto > limit))
    critical = [row for row in packets if row['traffic'] == 0]
    return dict(topology=folder.name, packets=packets,
                critical_packets=len(critical), deadline_misses=sum(p['deadline_miss'] for p in packets),
                critical_endpoint_crypto_alone_exceeds_deadline=sum(p['endpoint_crypto_exceeds_deadline'] for p in critical),
                observed_endpoint_crypto_min_ms=min(p['endpoint_crypto_ms'] for p in packets),
                observed_endpoint_crypto_median_ms=statistics.median(p['endpoint_crypto_ms'] for p in packets),
                input_sha256={name: hashlib.sha256((folder/name).read_bytes()).hexdigest()
                              for name in ['verification.json','uart_0.jsonl','uart_3.jsonl']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = dict(classification='Exploratory retrospective serial-stage accounting',
                  physical_measurement=False, timing_unit='emulator milliseconds',
                  interpretation='Matched sink signing and source verification are serial dependencies of the existing signed endpoint. Their observed sum excludes relay verification, routing, radio and other overhead. These samples are neither a universal lower bound nor evidence about an optimized backend or physical device. Repeated packets are not independent experimental replicates.',
                  rows=[diagnose(args.profile/(topology+'_100')) for topology in ['chain','choice']])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k not in ['packets','input_sha256']} for row in result['rows']], indent=2))

if __name__ == '__main__':
    main()

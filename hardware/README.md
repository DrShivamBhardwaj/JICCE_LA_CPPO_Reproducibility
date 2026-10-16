# Physical validation protocol and host radio adapter

Status: no physical sensor boards or measured current traces were available in this environment. The published 750 runs and new 30-fixture transport checks are simulations. The files here prepare a physical integration test; they are not a completed hardware validation or flash-ready board firmware.

## Required setup

Use four IEEE 802.15.4 radios configured as a multihop chain, a common host connected by USB serial, and a calibrated current/voltage logger. Record board/radio model, firmware commit, channel, transmit power, physical distances, antenna arrangement, host, instrument model, calibration, and synchronization method. Verify hidden endpoints cannot communicate directly. Coordinates are configured local deployment metadata. Include USB/host latency in reported end-to-end delay; no embedded inference/crypto latency claim follows from this host-driven adapter.

Firmware must implement newline JSON over 115200-baud serial:
- Host `{"command":"tx","token":1,"peer":1,"wire":"hex"}` sends these exact application bytes in a unicast IEEE 802.15.4 frame and echoes token in its MAC confirm.
- Board `{"event":"rx","peer":0,"wire":"hex"}` reports actual received bytes and MAC source; do not synthesize receptions.
- Board `{"event":"ack","token":1,"ok":true}` reports the MAC confirmation.
- Host `{"command":"telemetry"}` requests measurements; board response `{"event":"telemetry","energy_fraction":0.9,"queue":0}` must use measured/calibrated remaining energy and actual queue occupancy. Do not substitute a fixed energy value. A board-specific firmware port is required and is not included because no board target was provided.

Install pyserial and cryptography. Generate fresh private configurations with `python hardware/provision.py --output hardware/private_keys`. Never upload that directory. This supplies pairwise keys, a sink-only signing key and per-node boot sessions. Key distribution is out of band. Every restart requires fresh sessions/configurations on all nodes; persistent `.used` markers prevent reusing the same configuration after crash. No online key exchange, secure-element storage, encrypted payload or compromised-node telemetry truth guarantee is claimed.

Run one adapter per radio on the same host, using its private config and actual serial port:

```
python hardware/serial_adapter.py --config hardware/private_keys/node_0.private.json --port /dev/ttyACM0 --capture node0_capture.jsonl --packets 100
```

Run nodes 1–3 without source packets for the chain control. Stagger source traffic only after all nodes have acquired authenticated neighbor beacons. Then repeat with dropped frames, modified frames, replayed frames, and a compromised neighbor attempting to forge a sink receipt. Preserve unsuccessful runs. Record application/PHY byte overhead, delivered unique source identities, authenticated receipts, deadline violations, memory high-water mark and packet captures. Sink signing occurs only after a valid source authenticator and actual reception. Authentication cannot prevent a legitimate key holder from dropping packets or lying in its own telemetry.

Export current measurements with `time_s,voltage_v,current_a,provenance` columns (`provenance=physical`) and integrate using `python hardware/validate_measurements.py --current-csv measured_current.csv --output measured_energy.json`. Record the instrument's accuracy and sample interval. The label is an operator assertion, not an attestation. Compare radio-only current with complete board current; host CPU crypto is excluded from board readings. Hardware acceptance requires raw captures, instrument traces, calibration and an operator log. A blank template or software-generated trace does not satisfy it.

The prototype uses receipt-authenticated evidence and greedy progress routing. It does not carry over the attention policy's 750-run results; a separate policy integration and frozen overhead-aware study are needed before reporting performance for the new transport.

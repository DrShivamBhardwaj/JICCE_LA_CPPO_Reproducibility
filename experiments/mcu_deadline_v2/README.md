# Fixed LTO compiler pilot

Exploratory optimization chosen after the O3 failure. Freeze protocol and source hashes in a remote commit before execution. The endpoint remains source-verified Ed25519, with deadlines 90/350/1500 ms and 100 packets in each retained topology. No clocks, routing, keys, actor, crypto primitives, or acceptance rules change. LTO and default compiler loop optimization are the only changes. Original outputs remain intact. One build and one run per topology; retain failures. Emulator results do not establish physical timing, energy or production security.

Run via `.github/workflows/mcu-signed-deadline-lto.yml`. Functional acceptance is independent of deadline compliance.

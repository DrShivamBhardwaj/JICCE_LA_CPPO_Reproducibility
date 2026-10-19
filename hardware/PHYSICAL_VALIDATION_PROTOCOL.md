# Physical validation execution boundary

This protocol prepares the remaining validation; it is not a result.

## Embedded execution gate

The historical CC2538 bridge-only image used host routing and cryptography. The later Q22/O3 image executes routing, actor inference, HMAC and Ed25519 inside the emulated MCU, with private runtime provisioning; see `outputs/mcu_deadline_v1`. This integrated emulator result is not a physical-board firmware port or a production-security certificate. A physical port must preserve the tested feature mapping and endpoint and replace emulator-specific initialization and radio interfaces with the actual board drivers. Freeze the selected checkpoint and feature mapping, record RAM/flash usage, compare all feasible-choice logits/actions against host reference vectors, reject altered/replayed/wrong-session frames and verify standard HMAC/Ed25519 known-answer vectors. Then run the complete routed transport using that firmware. Standalone math or crypto known-answer tests alone do not validate integrated routing.

## Physical RF gate

Select the actual board revision and raw 802.15.4 driver. The proposed physical reference is four nRF52840 DK boards for a chain or six for the diamond. The current Renode CC2538 image is not an nRF52840 image. Implement clock/GPIO/radio initialization, flash the actual boards, record channel/TX power/antenna positions, collect independent over-air captures, and verify that non-neighbor links cannot bypass the topology. Retain every failed and successful run, with packet/session identities and timestamps.

## Current and energy gate

Use a calibrated current logger with documented supply voltage, sample rate, shunt/range, debugger exclusion and synchronization. Retain raw time/current/voltage samples, calibration record and instrument identity. Integrate joules over a specified boundary; measure or separately report host cost. A constant energy fraction and Renode/ns-3 modeled radio cost do not satisfy this gate. Profile the actual inference/crypto firmware, not an idle bridge, when making embedded energy claims.

## Availability

No physical boards, RF capture hardware or calibrated current logger were available to this execution environment. No measurements, calibration files or MCU inference/crypto results are invented. The paper remains a simulation/emulation study; these gates are required only to extend it to the corresponding physical/embedded claims.

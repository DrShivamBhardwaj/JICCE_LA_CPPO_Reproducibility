# Board choice and Android boundary

Recommended reference target: Nordic nRF52840 DK (PCA10056), with an IEEE
802.15.4-capable radio and supported Zephyr board definition. This recommendation
does not mean that our board-specific firmware has been built or tested.

| Item | Quantity | Purpose |
|---|---:|---|
| nRF52840 DK | 4 minimum | Source, two relays and sink for a physical chain |
| nRF52840 DK | 6 for the diamond | Match the six-node authenticated transfer topology |
| PPK2 or equivalent calibrated logger | At least 1 | Profile one node at a time |
| Synchronized probes or multichannel logger | As required | Concurrent whole-network energy measurement |
| Mac, powered USB hub and matching data cables | 1 setup | Existing host-driven serial software |

One instrument moved between nodes yields repeated per-node measurements. It
must not be described as simultaneous network-wide energy capture. Record the
instrument calibration, board revision, supply voltage, USB/debugger power
boundary, radio configuration and physical placement. Follow the DK current
measurement wiring documentation to avoid including the debugger's current or
powering a measured rail by an unintended second path.

## Android

An Android phone may support USB host/OTG and communicate with an external USB
radio through an appropriate Android application. Host capability, USB device
permissions, driver support and radio firmware are device-specific. The current
Python/pyserial host adapter is not an Android application and is not a drop-in
Android USB implementation.

Plugging the phone into the Mac does not turn it into one of our IEEE 802.15.4
nodes or a calibrated current instrument. Wi-Fi/Bluetooth traffic would be a
different link technology and must be evaluated separately. A phone could later
serve as a gateway, traffic source or display; external radio boards and a tested
Android bridge are still needed for this protocol. Even a phone with Thread
hardware does not establish app-level access to our raw MAC frame contract.

The user identified Android, but no exact model was supplied. USB/OTG and raw
radio compatibility therefore remain unverified. The observed Mac inventory on
16 October 2026 exposed no USB radio or Android USB device; only system and
Bluetooth serial endpoints were present. No phone or firmware was modified.

## Remaining physical work

1. Select the actual DK revision and SDK/toolchain version.
2. Implement and build its raw 802.15.4 TX/RX/MAC-confirm serial firmware.
3. Connect four or six boards and check the real radio topology.
4. Capture calibrated current, unique sink receptions and receipt verification.
5. Compare real measurements with the model without relabeling simulation data.

The original virtual API model does not execute MCU instructions. The separate Renode CC2538 backend now executes compiled firmware, as documented in renode_cc2538/README.md. It does not validate the physical nRF52840 port or replace these measurements.

Official sources checked 16 October 2026:

- https://www.nordicsemi.com/Products/Development-hardware/nRF52840-DK
- https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2
- https://docs.zephyrproject.org/latest/boards/nordic/nrf52840dk/doc/index.html
- https://developer.android.com/develop/connectivity/usb/host
- https://docs.nordicsemi.com/r/bundle/ug_nrf52840_dk/page/ug/dk/hw_measure_current.html

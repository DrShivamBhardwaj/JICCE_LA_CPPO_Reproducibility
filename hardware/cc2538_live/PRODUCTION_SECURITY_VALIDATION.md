# Production MCU validation: execution record not yet available

The current Renode image is not a flash-ready production board release. No secure boot, protected storage, readout protection or rollback capability is inferred from software HMAC/signature checks. Board selection must first establish which protections the chosen silicon actually supports.

| Test | Required evidence and acceptance | Current state |
|---|---|---|
| Board port and startup | Reviewed clock, linker, interrupt, UART and radio setup; real boot logs; board revision and toolchain hashes | Not executed |
| Key provisioning | Authenticated provisioning procedure; device identity binding; unauthorized reprovisioning rejected | Trusted emulator UART tested only |
| Key confidentiality | Document supported storage and debug protection; verify deployed debug/readout settings and key-extraction threat model | Not validated |
| Session persistence | Device-local monotonic state survives reset/power loss; interruption during update does not reuse sessions; exhaustion fails closed | Host allocator tested only |
| Firmware authenticity | Demonstrate supported authenticated update/boot mechanism; reject modified and rollback images under stated policy | Not validated |
| Receipt and replay controls | Execute existing negative controls on real RF traffic, across reboots, sequence wrap boundaries and queue pressure | Emulation controls only |
| Fault and resource behavior | Measure memory/stack, malformed packet handling, overload and recovery on the actual board | Tested emulated paths only |
| Side-channel/fault resistance | Declare attacker equipment/access and run a separate qualified assessment if claimed | No resistance claim |

Keep raw logs and artifact hashes. Record failures before remediation. A checked box or a generated report is not physical security certification. Store real serial numbers, provisioning material and sensitive assessment evidence outside the public repository.

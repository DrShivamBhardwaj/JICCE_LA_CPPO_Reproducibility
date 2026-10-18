# Separate remediation v1: reproduction and preservation

Start: `f9bf3c9382c73cee2f21fffa94e07f1a0affe415`.
Protocol freeze: `b24418008b318aa4a082e0a666c4a2196b5c994c`.
Pre-primary-outcome GCC portability amendment: `40a933ee06b0dd1521f7de36d4b215f9f8d8b9d4`.
The excluded first compile failure is retained under `outputs/remediation_v1/attempts`.

Use a fresh checkout/worktree. The runner refuses existing case directories; it does not overwrite retained experiments or selectively retry evaluation seeds. Preserve the original 750/180/240/600 families. New Cooja outputs belong only in `outputs/remediation_v1`; the compiler-only MCU profile belongs only in `outputs/mcu_deadline_v1`.

## GitHub execution

The checked-in workflows are the executable environment definitions:

- `.github/workflows/wsn-remediation.yml`: Ubuntu 24.04, Java 25, pinned Contiki/Cooja source revisions, native GCC, Python 3.12 and recorded Python packages. Two worker processes run the frozen 1,440-case list.
- `.github/workflows/mcu-signed-deadline.yml`: official Renode 1.17.0 portable distribution, verified archive SHA-256, Zig 0.15.1 and fresh private fixture material outside the public artifact. No fast-MAC endpoint replaces the signature endpoint.
- `.github/workflows/remediation-regression.yml`: full pytest discovery, pinned ns-3 3.44 wheel and all required native bridge builds. Building old powered-bridge controls against this wheel is regression compatibility, not a new execution of the historical 3.47 factorial.
- `.github/workflows/archive-audited-outputs.yml`: completed successful studies receive an immutable run-tagged release with raw captures, compiled images, environment and a manifest. Failure artifacts remain failures.

Select the relevant workflow and **Run workflow** on a clean revision. Running it again creates a new execution; it does not retroactively replace the recorded run. Commit changed scientific mechanisms/protocol amendments before observing their outcomes.

## Equivalent shell commands

Install the dependencies and Java version specified by the workflow, then:

```bash
python experiments/remediation_v1/run.py --verify-only
PYTHONPATH=src python -m pytest -q tests/test_remediation_v1.py tests/test_remediation_endpoints.py
python experiments/remediation_v1/diagnostics.py --output outputs/remediation_v1/archive_diagnostics
bash experiments/remediation_v1/bootstrap.sh
python experiments/remediation_v1/run.py --execute --workers 2
python experiments/remediation_v1/analyze.py
python scripts/verify_remediation_archive.py --dataset outputs/remediation_v1 --output outputs/remediation_v1/integrity_recheck.json
python scripts/summarize_remediation_secondary.py
python scripts/profile_mcu_remediation.py
python scripts/plot_remediation_evidence.py
```

The final three reporting commands require their corresponding completed captures. No command should label partial execution as the completed factorial. Per-case audit acceptance checks completeness and reconstruction, not perfect packet delivery: attack-induced losses and late deliveries remain outcomes, and do not satisfy the separate original deadline gate. Capture/image hashes bind the output to the case list; they are not physical provenance or protection against coordinated archive replacement.

## Document reproduction

After complete audited data and plot exports exist, `python scripts/build_array_manuscript.py` rebuilds the integrated Word draft. Run `python scripts/audit_array_manuscript.py`. To check preservation against the exact starting paper, retrieve `publication/array/Array_Manuscript.docx` at the starting commit into a separate path and run `python scripts/audit_array_remediation.py --baseline PATH`.

Render Word with LibreOffice or the document renderer and inspect every page before releasing the PDF. Font and office-renderer changes may change pagination. Tables, native equations, prior images and historical statistics must remain intact. New table values must match `analysis.json`; plot exports must come from the verified captures.

## Interpretation

Geometry blocks are the primary experimental units. Radio seeds, packets, interventions and repeated checkpoint use do not create additional independent topology or training replicates. Public fixture keys do not establish confidential-key deployment security. Scheduled Cooja delays overlap per packet; they are not serial MCU CPU simulation or physical timing. Renode stage timings are emulator observations. No reproduction command supplies physical current/RF measurements, protected key storage, actual author consent or authenticated portal approval.

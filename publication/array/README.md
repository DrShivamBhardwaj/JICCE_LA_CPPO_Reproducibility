# Array manuscript package

The active extended manuscript contains a 232-word abstract, ten native editable equations, eleven embedded figures, nine editable tables and 24 references. Algorithm 1 has 17 numbered lines with three indentation levels.

The unchanged 750-run feedback benchmark and separate 180-run authenticated policy-transfer evaluation are distinguished from host-controlled PTY/ns-3 and compiled CC2538/Renode bridge controls. The exploratory extension includes 18 stress runs and 33 sensitivity runs. These results do not establish attention superiority, embedded inference/cryptography, measured battery lifetime or physical RF validation.

See [section-wise editorial review](../../docs/ARRAY_SECTION_BY_SECTION_EDITORIAL_REVIEW.md) for critique, rewritten passages, equation definitions and figure cross-references. The editorial preservation audit verifies unchanged equations, table XML, nine unchanged figure image hashes and one revised lifecycle figure, numerical literals, source hashes and fixture IDs. `editorial_changes.json` records all 36 revised paragraphs.

Rebuild with `scripts/build_array_manuscript.py`; review the rendered pages before replacing the PDF. Run `scripts/audit_array_manuscript.py`, `scripts/check_review_math.py`, `scripts/audit_array_figure_values.py`, and `scripts/audit_array_editorial.py --baseline PATH_TO_PRECEDING_DOCX`. The baseline for the current editorial pass is commit 9d56b207bfed0bca9b691f364c4ff2c6d280a4bd.

The figure pack contains editable SVG, vector PDF and 600-dpi PNG artwork. Highlights.txt contains four highlights below 85 characters each. Consult [review resolution](../../docs/PEER_REVIEW_RESOLUTION_20261016.md) and [submission checklist](../../docs/ARRAY_SUBMISSION_CHECKLIST.md) for remaining scientific and author declaration requirements. This is an Array-targeted review draft; it has not been submitted or certified for acceptance.

Executed post-freeze evidence is integrated into Sections 5.6–5.7: 240 factorial runs, 27 power/sleep diagnostics and isolated Cortex-M3 actor/crypto tests. The original 750-run and 180-run evidence families remain separate. See Postfreeze_Validation_Addendum.md and ../../docs/COMPLETION_MATRIX_20261018.md. Integrated CC2538 execution, physical measurements and author/portal approvals are still open.

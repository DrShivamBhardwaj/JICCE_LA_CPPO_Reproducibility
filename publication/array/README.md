# Array manuscript package

The active 22-page manuscript contains a 198-word abstract, ten native editable equations, ten embedded figures, seven editable tables and 22 references. Algorithm 1 has 17 numbered lines with three indentation levels.

The unchanged 750-run feedback benchmark and separate 180-run authenticated policy-transfer evaluation are distinguished from host-controlled PTY/ns-3 and compiled CC2538/Renode bridge controls. The exploratory extension includes 18 stress runs and 33 sensitivity runs. These results do not establish attention superiority, embedded inference/cryptography, measured battery lifetime or physical RF validation.

See [section-wise editorial review](../../docs/ARRAY_SECTION_BY_SECTION_EDITORIAL_REVIEW.md) for critique, rewritten passages, equation definitions and figure cross-references. The editorial preservation audit verifies unchanged equations, table XML, figure image hashes, numerical literals, source hashes and fixture IDs. `editorial_changes.json` records all 35 revised paragraphs.

Rebuild with `scripts/build_array_manuscript.py`; review the rendered pages before replacing the PDF. Run `scripts/audit_array_manuscript.py`, `scripts/check_review_math.py`, `scripts/audit_array_figure_values.py`, and `scripts/audit_array_editorial.py --baseline PATH_TO_PRECEDING_DOCX`. The baseline for the current editorial pass is commit 9d56b207bfed0bca9b691f364c4ff2c6d280a4bd.

The figure pack contains editable SVG, vector PDF and 600-dpi PNG artwork. Highlights.txt contains four highlights below 85 characters each. Consult [review resolution](../../docs/PEER_REVIEW_RESOLUTION_20261016.md) and [submission checklist](../../docs/ARRAY_SUBMISSION_CHECKLIST.md) for remaining scientific and author declaration requirements. This is an Array-targeted review draft; it has not been submitted or certified for acceptance.

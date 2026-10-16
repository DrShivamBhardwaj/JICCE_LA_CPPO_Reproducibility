# Array manuscript package

Array_Manuscript.docx preserves ten native editable equations and includes eight figures, six tables and 21 references. It combines the unchanged 750-run feedback study with a separate 180-run authenticated policy-transfer evaluation and separate PTY/ns-3 and compiled CC2538/Renode firmware integration controls. The results do not establish an attention advantage or physical hardware validation.

Highlights.txt contains four highlights, each below 85 characters. figures/ now contains all eight redesigned figures as editable SVG, vector PDF and 600-dpi PNG. The Word manuscript embeds the new figures. Historical artwork remains unchanged under publication/redesigned/figures/. The manuscript is an Array-targeted review draft, not a certification of editorial suitability or portal compliance.

See docs/ARRAY_TARGET_AND_VIRTUAL_STATUS.md for journal fit, verified publisher information, reproducibility instructions and remaining scientific limitations. No manuscript has been submitted.

Rebuild the active artwork with scripts/build_array_journal_figures.py and audit the exact plotted effects with scripts/audit_array_figure_values.py before running scripts/build_array_manuscript.py. The source-value ledger, fingerprints and 33-interval audit are included with the figures. SciSpace/Scientific Manuscript Architect review notes are in docs/FIGURE_REDESIGN_REVIEW.md.

Language and layout revision (2026-10-16): 57 scientific paragraphs edited for clear academic English; all eight figures, six editable tables and Algorithm 1 now sit in the body near their discussion. The 195-word abstract and 20-page rendered manuscript retain the numerical evidence, 10 native equations and 21 references. See `manuscript_audit.json` and `../../docs/MANUSCRIPT_LANGUAGE_AND_LAYOUT_REVIEW.md`.

Peer-review revision: current manuscript has 22 pages, 10 embedded figures, 7 editable tables and 22 references. Source-derived plots include 18 new 60/300 s stress runs and 33 coefficient-sensitivity runs. See `../../docs/PEER_REVIEW_RESOLUTION_20261016.md` for corrections, negative results and unresolved deployment validation. The new runs are exploratory and leave frozen evidence unchanged.

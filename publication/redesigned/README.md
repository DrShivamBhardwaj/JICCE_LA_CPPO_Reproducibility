# Focused manuscript redesign

Current title: Receipt Assisted Passive Feedback for Multihop Wireless Sensor Routing.

The main manuscript concentrates on the frozen 750-run feedback experiment. Historical failed architecture studies remain in the repository and the earlier complete evidence manuscript. The redesign changes presentation and interpretation, not frozen implementation, checkpoints, traces, the 60-test family or gate.

## Files

- JICCE_Redesigned_Manuscript.docx and PDF: 23-page review draft with 10 native equations, 19 references, 5 tables and 6 figures.
- figures/: editable SVG, vector PDF and 900-dpi PNG; generated from canonical results.
- interactive_architecture.html: download and open in a browser; component selection explains radio and simulator state boundaries. This is an explanatory schematic, not another simulator.
- interactive_architecture.fragment.html: inline source for the same explainer.
- scispace_search_record.json and reference_verification.json: discovery record and verification depth. Automated SciSpace limitation summaries were not used to assert that a paper omitted tests.
- document_checks.json: document and interaction QA scope.

The figures use paired estimation graphics. Whiskers are unadjusted paired 95% intervals over 30 fixtures; corrected decisions remain in the 60-test Holm family. Energy panels distinguish total radio joules from energy per delivered payload byte. Figure 3 uses a PRISMA-inspired experimental accounting layout; this is not a systematic review.

## Rebuild

From the repository root, install requirements-redesign.txt in an isolated environment, in addition to the simulation dependencies. Run:

```bash
python scripts/audit_censored_implementation.py
python scripts/build_redesigned_figures.py
python scripts/build_redesigned_manuscript.py
node scripts/test_interactive_architecture.cjs
```

The Word renderer additionally requires LibreOffice; its PDF is inspected after rendering. The interactive test checks the JavaScript at DOM level at four widths. Browser screenshot QA was unavailable because the browser binary download failed; no browser rendering pass is claimed.

The draft follows the retrieved JICCE review-text instructions. The corresponding author's phone/fax fields, submission forms and coauthor approval are not invented. Publication novelty, final length and editorial fit require author/editor judgment. This package has not been submitted.

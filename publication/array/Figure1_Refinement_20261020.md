# Figure 1 — matched feedback interventions (final minimal artwork)

This version is additive. It does **not** overwrite the older `fig1_architecture.svg` belonging to the archived benchmark manuscript.

- **Tracked, editable figure:** [figures/fig1_matched_feedback_refined.svg](figures/fig1_matched_feedback_refined.svg)
- **Short caption:** *Fig. 1. Matched feedback interventions and forwarding path.*
- **Presentation:** four monochrome, horizontal stages; four matched 2 × 2 factorial arms in one compact legend. The run-count and legacy-reference notes were removed **from the image only**.
- **Scope:** controlled 1,440-case matched factorial intervention, not the separate later 2,880-case geometry study.
- **Scientific controls:** same own-first-hop ACK gate, 150 ms expiry and late/positive credit; fixed Q22 actor; proofs in these four arms incur traffic cost but do not earn routing-ledger feedback credit.
- **Underlying final raster approved for Word:** 2164 × 600 PNG; SHA-256 `824c29ccf711e0885fcc3c09b247a30772cce0f8d7bc6eeda87003932601d68c`. The tracked SVG is the **editable vector counterpart**, not a byte-identical copy of the approved PNG.

## Paragraph surrounding Figure 1

Figure 1 shows the two controlled interventions before the unchanged evidence and forwarding stages. Negative updates determine whether an eligible but unconfirmed forwarding attempt adds a failure penalty at expiry. Proof generation independently controls authenticated feedback-frame traffic. The four combinations isolate these choices under a shared routing policy.

Each matched arm uses the same first-hop ACK gate, 150 ms expiry, positive-credit weight and treatment of late evidence. After an ACK, the source waits for eligible forwarding evidence; in a negative-update arm, an unconfirmed record receives the cached expected-link failure increment once. A later positive observation does not undo that penalty. The proof-enabled arms produce authenticated frames and incur airtime and scheduled-processing costs, but their proof frames are excluded from ledger credit across the four matched arms. Consequently, the proof factor measures additional traffic and delay, not the benefit of using proof evidence for routing decisions. The separate legacy active-proof reference follows different evidence-eligibility and expiry rules and is excluded from the factorial contrasts.

## Current submission-document provenance

The revised manuscript was independently finalized as `Array_Manuscript_4320_Runs_Figure1_Refined.docx` (SHA-256 `fafc8f529068328586e142663b7965d1c5c8244fc914e2c05d0b68a113a32c7f`, 18 figures, 14 tables). **That binary DOCX is not part of this commit.** Do not substitute the older tracked `publication/array/Array_Manuscript.docx` for this latest submission version.

The repository's source branch is a draft PR; merging or publishing a journal-submission document is a separate editorial decision.

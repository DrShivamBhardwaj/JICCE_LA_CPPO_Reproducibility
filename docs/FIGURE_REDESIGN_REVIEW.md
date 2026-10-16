# Array figure redesign and scientific review

All eight figures are programmatically authored vector artwork or plots from retained observations. SVG/PDF/600-dpi PNG exports are provided. This is not a claim that the images were drawn by a human or independently peer reviewed.

Scientific Manuscript Architect was applied to panel hierarchy, concise captions, typography, line weights, explicit units, and interpretation of uncertainty. SciSpace was used to search and extract limitations for energy-model and network-reproducibility literature. Its summaries are advisory; they are not full-text replication or evidence for new numerical claims.

SciSpace search question: How should paired simulation experiments in wireless sensor network routing report effect sizes, uncertainty intervals and energy accounting so that figures distinguish reproducible integration evidence from policy superiority?

Selected records consulted:
- Harrison et al., Busting myths of energy models for wireless sensor networks. DOI 10.1049/EL.2016.1591.
- Lamela et al., Repeatable and Reproducible Wireless Networking Experimentation through Trace-based Simulation. DOI 10.1109/WIMOB.2019.8923120.
- Jacob et al., TriScale: A Framework Supporting Reproducible Performance Evaluations in Networking. SciSpace returned the repository record DOI 10.5281/ZENODO.3656819. Its limitations extraction explicitly lacked enough context; no limitation was inferred from that absence.

Design decisions:
1. Keep the 750-run benchmark, 180-run transfer and firmware emulation boundaries separate.
2. Show all paired observations in Figures 5 and 8; diamonds show empirical means, not additional observations.
3. Read intervals from the retained analysis files; do not regenerate significance tests or select outcomes for appearance.
4. Figures 4–6 retain unadjusted paired t intervals. Figure 8 retains exploratory paired bootstrap intervals; neither is relabeled as a multiplicity-adjusted confidence band.
5. Separate modeled total radio energy, energy per delivered byte and PHY traffic. No physical battery-saving claim follows from these figures.
6. Figure 3 uses PRISMA-inspired experimental accounting, not systematic-review screening.
7. Figure 7 distinguishes a PTY firmware API from actual compiled C execution in Renode and labels host-side inference/crypto.

Rebuild: python scripts/build_array_journal_figures.py, then python scripts/build_array_manuscript.py. The plot-value ledger and input SHA-256 hashes are in publication/array/figures/. All original results, checkpoints and historical figures remain unchanged.

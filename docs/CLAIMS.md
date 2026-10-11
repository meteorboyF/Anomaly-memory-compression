# Claims ledger

A claim enters the manuscript only with status **supported**: N ≥ 3 paired
seeds, complete manifests from a clean SHA, mechanism check passed, and a
delta literature sweep that month. The wording here is the ceiling for the
manuscript wording. Failed hypotheses and negative results stay listed.

| # | Claim (one sentence, with numbers once measured) | Evidence (manifest ids) | Status |
|---|---|---|---|
| C0 | Our metric implementation reproduces the official MVTec AD AU-PRO, PRO curve and image AUROC (max abs. deviation ≤ 3e-8 on 200 randomized cases plus the official toy example) | `metric_selfcheck` (laptop run 2026-10-11, dirty tree, NOT citable; citable Colab run pending) | infrastructure, pending citable run |
| C1 | Under P-REPRO, our PatchCore reproduction matches published mean image AUROC (99.1) and pixel AUROC (98.1) within tolerance | — | planned (Phase 1) |
| C2 | Under P-STUDY, PatchCore AU-PRO@0.3 matches the no-crop re-run of 92.7 within ±1.0 | — | planned (Phase 1) |
| C3 | At 1 % memory (greedy), the compression penalty on small (<0.1 %) regions differs from that on large (≥1 %) regions by D = … [95 % CI …]; verdict per H-01.5 (supported / informative null / inconclusive) | — | registered, not run |
| C4 | PaDiM byte points vs coreset arms on the same size-stratified AU-PRO axes (descriptive) | — | registered, not run |
| — | (withdrawn 2026-10-11, D-016) any coverage-preserving correction or mechanism claim | — | withdrawn |
| — | Dataset statistics (counts, defect area distribution, defects lost to the centre crop) | `profile_data` | pending Colab Cell 3 |

## Negative results / failed hypotheses

(none yet)

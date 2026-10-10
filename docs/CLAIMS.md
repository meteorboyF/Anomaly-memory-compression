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
| C3 | At 1 % memory, aggregate metrics change by < 1 pt while the small-region AU-PRO penalty exceeds the large-region penalty by D = … (H-01) | — | registered hypothesis, not run |
| C4 | The size asymmetry follows coverage loss (mechanism check H-01 a–c) | — | registered, not run |
| — | Dataset statistics (counts, defect area distribution, defects lost to the centre crop) | `profile_data` | pending Colab Cell 3 |

## Negative results / failed hypotheses

(none yet)

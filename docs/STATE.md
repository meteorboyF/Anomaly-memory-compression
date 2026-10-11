# STATE — single source of truth (update every session)

_Last updated: 2026-10-11, session 2._

## Frozen topic (D-016, researcher-approved wording)

> At fixed feature extraction and measured memory budgets, does memory-bank compression disproportionately reduce industrial anomaly segmentation performance on small defects?

- **Benchmark:** original MVTec AD, 15 categories, official splits, existing masks.
- **Contribution:** a controlled empirical study, pre-registered in REALITY_CHECK H-01 v2.
- **No correction or method is promised.** Any future method needs separate evidence, literature review and approval.

Novelty verdict: **CROWDED, rescoped**, conditional on reading BAMB (LITERATURE §1.3).

## Phase 0: in progress. Gate NOT approved. Accelerator use: 0 CU.

`configs/control/gates.yaml` has every phase unapproved. `allocations.yaml` is empty, so all GPU tools refuse.

### Completed (with evidence)

| Item | Evidence |
|---|---|
| Infrastructure, safeguards, Colab runner | 80 CPU tests; CI green; cold clone passes; pre-commit hook refused a planted token |
| Metric replica vs official MVTec code | Laptop run: max deviation 3e-8. A **citable** run comes from Colab Cell 3 |
| Size-stratified evaluator: one global sort, every bin and both FPR limits | Equals separate per-bin official computations (test). Native-resolution cost measured: ≈52 MB and ≈0.4 s per 1024² image |
| Paired bootstrap / equivalence statistics | `eval/stats.py`, synthetic tests (effect detected; null classified as equivalent; inconclusive rule) |
| Literature | 3 passes plus full-text reading of Costanzino, HR-Pro and Tu 2026 |
| Protocol, pre-registration, baselines | H-01 v2 complete; PaDiM chosen (D-017) |
| Venue | Pattern Recognition first (D-010) |

### Blockers and pending items

1. **CPU data verification (Colab Cells 1→2→3→11). NOT yet run.** None of these items is complete until its output is checked:
   - [ ] archive downloaded, our SHA-256 recorded, Drive copy re-verified, marker written
   - [ ] 15 categories present; per-category counts equal IJCV Table 1 (3629 / 467 / 1258)
   - [ ] every defective test image has a mask; no orphan masks; image and mask sizes equal
   - [ ] split checks: train contains only `good`; good test images have no mask
   - [ ] leakage: exact file and pixel duplicates across train/test and across categories
   - [ ] mask value sets binary
   - [ ] dataset_hash and split_hash recorded
   - [ ] pre-registered S/M/L counts per category (regions, images by largest component, mixed images), then the merge rule applied if needed
   - [ ] citable metric self-check (clean SHA)
   - [ ] evaluator sanity: P-REPRO crop and native P-STUDY (constant ≈0.15 AU-PRO, oracle 1.0)
   - [ ] Cell 11 artifact verification
2. **BAMB unread** (closed access; no abstract anywhere we can reach). The novelty verdict is conditional on it.
3. **No Colab CU rate observed yet.** The pilot's CU cap cannot be set.
4. **Your decisions:** the Phase 0 gate, the pilot allocation, and MVTec's form question.
5. **Phase 1 code** (extraction, coreset, scoring, PaDiM) is written only after gate approval.

## Exact next commands

Colab, **CPU** runtime:

```
Cell 1  -> Cell 2 (acquire_data) -> Cell 3 (metric_selfcheck, profile_data,
evaluator_sanity, evaluator_sanity_native) -> Cell 11; then Runtime > Disconnect and delete runtime
```

Then paste the outputs into chat. Drive keeps a copy of every log under `artifacts/logs/`.

## What the units bought

Nothing. No units have been spent.

## Next single most important question

Do the mask-derived S/M/L counts allow ≥5 categories with ≥10 S **and** ≥10 L regions? If not, the pre-registered merge ("<1 %" vs "≥1 %") applies before any model output exists.

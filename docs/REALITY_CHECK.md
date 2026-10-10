# Reality check: registered hypotheses and outcomes

Format: `01_RESEARCH_METHOD.md`. Every entry receives an Outcome, including
failures. The strata, metrics and tests below were fixed on 2026-10-11,
before any model output existed. Only the outcome-free data profile may be
consulted afterwards, and only to apply the merge rule written here.

---

```
H-00  2026-10-11  status: PROPOSED (needs gate + CU approval)
Question: does the Colab pipeline run end to end, at what measured cost?
  Pipeline: extraction -> nested greedy coreset -> kNN scoring
  -> raw score grids -> CPU evaluation.
Scope: 2 categories x 1 seed, P-STUDY geometry.
  toothbrush: smallest train set.
  hazelnut: largest train set, the cost upper bound.
  Greedy coreset run to 10%; prefixes give 0.1/1/5%. Random selector at
  matched bytes. Uncompressed reference.
Success: all artifacts written with complete manifests; a deliberate
  interrupt-and-resume reproduces identical coreset indices; per-category
  throughput measured (images/s, coreset iterations/s, peak VRAM, bank bytes).
Not a scientific test: nothing from H-00 enters CLAIMS.md. Its predictions
  are evaluated only to check the pipeline.
Cost: provisional, <= 1.5 T4 wall-hours including setup and staging
  (COMPUTE_LEDGER).
Outcome: (pending)
```

---

```
H-01  2026-10-11  status: REGISTERED (runs only after Phase 1 reproduction passes)
Hypothesis: at matched memory bytes, compressing the normal-patch memory of a
  PatchCore-style detector reduces sensitivity to SMALL defects more than to
  large ones. Mechanism: compression loses coverage of normal neighbourhoods,
  which inflates normal scores, shrinks the score margin of small defects
  and leaves large defects unchanged.

Setting:
  Dataset and protocol: MVTec AD, 15 categories, official splits, P-STUDY
    (no crop, native-resolution GT, maps rebuilt by bilinear upsampling +
    Gaussian sigma=4).
  Model: PatchCore (official algorithm), WRN-50 layers 2+3.
  Budgets, given as bytes, with ratios alongside: B in {0.1%, 1%} PRIMARY;
    {5%, 10%} SECONDARY.
  Reference: uncompressed memory (100%). If it is infeasible, the 10% coreset
    is the reference instead, and this is declared before the run.
  Selectors: approximate greedy k-centre (PatchCore) [primary]; random
    [control]. Both at matched bytes.
  Seeds: 3 paired seeds (0, 1, 2). Within a seed, every arm shares the
    projection and start points (greedy) or the RNG stream (random).

Size definitions (native resolution, from supplied masks only):
  Region level (localisation): 8-connected GT component; size = region pixels
    / image pixels.
  Image level (detection): total mask pixels / image pixels.
  Bins, PRE-REGISTERED and absolute: S < 0.1%; M 0.1% to <1%; L >= 1%.
  Merge rule: a category x bin cell with < 10 items (regions or images) is
    not reported per category. A pooled bin with < 30 items is merged into its
    neighbour (S into M first), and the merge is reported.
  Secondary strata: within-category tertiles of region size from the
    outcome-free profile. These control for category, since categories
    differ in both defect size and difficulty.

Metrics:
  Localisation: AU-PRO@0.3 restricted to the regions of one size bin. The FPR
    is computed over all defect-free pixels of the category's test set (the
    official definition with a region filter).
  Detection: image AUROC of the bin's defective images against all good test
    images of the category.
  Secondary: AU-PRO@0.05.
  Official aggregates are always reported alongside: image AUROC, pixel
    AUROC, AU-PRO@0.3 and @0.05, per category and macro-mean.

Primary contrast:
  Penalty: Delta_b(B) = metric_b(reference) - metric_b(B), per category and
    seed.
  Contrast: D(B) = Delta_S(B) - Delta_L(B).
  Unit of analysis: the category, using the mean over 3 seeds. Only
    categories with valid S and L cells are included.
  Test: two-sided Wilcoxon signed-rank on D across categories, for each
    primary budget x primary metric (2 x 2 = 4 tests), Holm-corrected.
  Effect size: Hodges-Lehmann median with a 95% bootstrap CI over categories.
    The seed SD of D is reported as well.

Prediction:
  D(1%) > 0, AU-PRO@0.3 points, in the band +1 to +5.
  D(1%) for image AUROC in the band 0 to +2 points.
  D(0.1%) larger than D(1%).
  The aggregate macro AU-PRO@0.3 penalty at 1% stays < 1 point (the "parity"
    claimed in the literature).

Falsified if any of the following holds:
  1. All four Holm-adjusted p >= 0.05.
  2. |median D| < 2 x the seed SD of D.
  3. D > 0 in fewer than 2/3 of valid categories.

Mechanism check (must pass before any coverage claim):
  (a) At budget B, the inflation in nearest-neighbour distance of NORMAL test
      patches must be measurable.
  (b) The small-bin penalty must co-vary with the loss of margin
      m = max score in region - 99th percentile of good-image pixel scores.
  (c) The random selector at matched bytes must show a LARGER size asymmetry
      than greedy, because k-centre is the coverage-preserving selector.
  If D > 0 but (a) and (b) fail, the effect is attributed to a confound
  (resolution, smoothing, region-size statistics), not coverage, and is
  reported that way.

Abandon:
  The coverage-preserving correction (H-02) is NOT built if H-01 is falsified
  at both primary budgets. The finding is then written up as a pre-registered
  null: "compression down to X bytes is size-neutral on MVTec AD within the
  CI".
  The researcher decides whether that null is worth a paper or the project
  stops.

Risks: Costanzino et al. (2025) report MVTec AD as comparatively size-stable,
  which lowers the prior on H-01. VisA is not added without separate
  verification.
Cost: provisional (COMPUTE_LEDGER, grid G1). Measured pilot throughput
  replaces it before approval.
Outcome: (pending)
```

---

```
H-02  (NOT REGISTERED; placeholder)  coverage-preserving normal-only correction
Pursued only if H-01 passes AND its mechanism check passes.
It must then beat, at matched bytes:
  - PatchCore greedy;
  - random selection;
  - the density comparator;
  - an HR-Pro-style residual-coverage variant.
Registration happens before any implementation.
```

---

## Phase 1 reproduction targets (registered 2026-10-11)

| Protocol | Quantity | Published | Source | Tolerance |
|---|---|---|---|---|
| P-REPRO | PatchCore WRN-50, 10 % coreset, mean image AUROC | 99.1 (paper) / 0.9916 (official results CSV) | Roth et al. 2022; repo results | ±0.5 pt |
| P-REPRO | mean pixel AUROC (224 crop) | 98.1 / 0.9811 | same | ±0.3 pt |
| P-STUDY | mean AU-PRO@0.3, official script, no crop | 92.7 (PatchCore re-run by EfficientAD's authors) | Batzner et al. WACV 2024 | ±1.0 pt |

If a reproduction falls outside tolerance, it is investigated before Phase 2,
as the playbook requires. The usual causes are preprocessing, the PRO variant,
and image-score aggregation.

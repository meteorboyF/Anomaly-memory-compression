# Reality check: registered hypotheses and outcomes

Format: `01_RESEARCH_METHOD.md`. Every entry receives an Outcome, including
failures.

This version (v2, 2026-10-11) supersedes v1 of H-01. It freezes the rescoped
topic and completes the protocol. It was written before any model output
existed. The only data consulted afterwards will be the outcome-free profile
(mask-derived bin counts), and only to apply the merge rule written here.

**Frozen topic (D-016).** At fixed feature extraction and measured memory
budgets, does memory-bank compression disproportionately reduce industrial
anomaly segmentation performance on small defects?

The contribution is a controlled empirical study. No method or correction is
proposed. Any later method proposal needs separate evidence, a separate
literature review and separate approval.

---

```
H-00  2026-10-11  status: PROPOSED (needs gate approval + an explicit CU allocation)
Purpose: execution, resume reliability and measured cost. NOT hypothesis
  testing.
Scope:
  Categories: hazelnut and screw.
  Seed: 0.
  Protocol: P-STUDY.
  Arms:
    - uncompressed reference;
    - greedy coreset to 10% (nested prefixes give 5/1/0.1%);
    - random selector at matched bytes;
    - PaDiM-Rd100 (one byte point).
Outcome blinding: no size-stratified comparison is computed or inspected from
  pilot outputs.
  The pilot evaluation is limited to:
    - pipeline sanity (aggregate image AUROC > 0.5 for every arm);
    - manifest validity.
  Pilot predictions are kept. Stratified analysis runs only once the full
  pre-registered grid exists, with the protocol below unchanged.
Success:
  - all artifacts complete and verified;
  - a deliberate interrupt-and-resume yields byte-identical coreset indices;
  - coreset prefix equality holds (D-011);
  - per-category throughput and memory are measured.
Outcome: (pending)
```

---

```
H-01  2026-10-11  status: REGISTERED v2 (runs only after Phase 1 reproduction passes)
```

## H-01.1 Fixed system (P-STUDY). Identical for every arm of the primary comparison

| Component | Fixed value |
|---|---|
| Data | MVTec AD, 15 categories, official splits; memory built from `train/good` only |
| Input | RGB (grayscale replicated to 3 channels). Resize to 256×256 (bilinear, torchvision rule). **No crop.** ImageNet mean/std |
| Backbone | WideResNet-50-2, torchvision `IMAGENET1K_V1` weights (weights-file SHA-256 recorded); frozen; `torch.inference_mode()` |
| Features | layer2 + layer3. 3×3 local neighbourhood aggregation (PatchCore `patchsize=3`). Each layer adaptively pooled to 1024 then averaged: **1024-dim** patch features on a **32×32** grid (stride 8 at 256 px) |
| Precision | **fp32** for extraction, bank storage and search. No mixed precision in the primary comparison |
| Scoring | exact L2 nearest neighbour, **k = 1** (`anomaly_scorer_num_nn=1`, as in the official baseline script). Image score = max patch score |
| Maps | 32×32 patch scores → bilinear to 256×256 → Gaussian σ = 4 px → bilinear to native resolution. Evaluated against native masks |
| Selectors | approximate greedy k-centre (official: random projection to 128 dims, 10 start points) [primary]; uniform random patch subset [control] |
| Budgets | reference = **uncompressed** bank (100 %). Compressed = 10 % (PatchCore default), 1 %, 0.1 % of the category's train patches, all reported in bytes |
| Seeds | 0, 1, 2. Within a seed every arm shares the same projection, start points and RNG stream |
| Tuning on test masks | **none.** Every setting above is fixed from the official PatchCore code or by convention, before data |

If the pilot shows the uncompressed reference is infeasible on the approved GPU, the reference becomes the 25 % coreset. That decision is recorded before any full-grid run, and the primary budget comparison is unchanged.

**Memory accounting (D-019).** The persistent footprint of an arm is

  bytes = n_vectors × 1024 × 4 (fp32) + index overhead.

- Search is brute-force exact (flat L2), so the overhead is the serialized index header only, measured from the saved index file.
- The 1024×128 random projection exists only during selection. It is not persistent and not counted, but it is reported.
- PaDiM bytes = H′·W′·(d + d²)·4: per-position mean plus inverse covariance at fp32. It is measured from the stored arrays.
- Backbone weights are excluded from every arm, since they are identical across arms, and reported once.

## H-01.2 Size unit and multi-defect images

- **Primary unit: connected component.** A component is an 8-connected ground-truth region at **native resolution**. Its size is the component's pixel count divided by the image's pixel count.
- **Bins** (absolute, pre-registered):

  | Bin | Area fraction | Meaning |
  |---|---|---|
  | S | < 0.1 % | smaller than one 8×8 feature cell at 256 px (1/1024 of the image) |
  | M | 0.1 % to < 1 % | 1–10 cells |
  | L | ≥ 1 % | more than 10 cells |

  The S boundary therefore separates defects below the feature grid's resolution from those above it.
- **Multi-defect images.** In the primary analysis each component is evaluated in its own bin. For a bin's AU-PRO curve:
  - PRO averages only over that bin's components;
  - FPR uses every defect-free pixel of every test image;
  - pixels of components from other bins count as neither positive nor normal.

  This is the official AU-PRO definition with a region filter.
- **Secondary (detection):** image-level AUROC per bin. A defective image takes the bin of its **largest** component, because the max-score image statistic is driven by the most salient region. Images whose components span several bins are counted as "mixed" and also reported with mixed images excluded.
- **Cell rules:**
  - A category × bin cell is reportable only with ≥ 10 regions (or images).
  - A category enters the primary contrast only if both its S and L cells are reportable.
  - If fewer than 5 categories qualify, S is merged into M ("<1 %" vs "≥1 %") and that merge is reported.

  These counts come from masks only (`profile_data`, Cell 3).

## H-01.3 Comparison

For category *c*, seed *s* and bin *b*, the compression-induced change is

  Δ_b(B) = AUPRO_b@0.3(reference) − AUPRO_b@0.3(budget B),

and the primary contrast is

  **D(B) = Δ_S(B) − Δ_L(B).**

D > 0 means compression costs small defects more. It is averaged over the 3 seeds within each category, then macro-averaged over qualifying categories.

- **Primary test:** a single test, **D at B = 1 %**, greedy selector. 1 % is the budget at which the literature reports aggregate parity.
- **Secondary**, Holm-corrected as a family and labelled secondary:
  - D at 0.1 % and at 10 %;
  - D with AU-PRO@0.05;
  - D for the M bin (Δ_M − Δ_L);
  - D for image-level AUROC strata;
  - D under the random selector.

  Official aggregates (image AUROC, pixel AUROC, AU-PRO@0.3 and @0.05, per category and macro) are always reported next to the strata.

## H-01.4 Uncertainty and the repeated-measures structure

**Paired, stratified image bootstrap** (`eval/stats.py`), with B = 2000:

- Within each category, normal and defective test images are resampled with replacement separately.
- The same resampled multiset is applied to every arm and every seed. Repeated measurements of an image across memories and seeds stay paired, and regions move with their image.
- Categories are fixed strata: all 15 are the population of interest.
- Seeds enter through the seed mean. Their SD is reported, and the sign of D must agree on all three seeds.
- Point estimates use the exact official AU-PRO. The bootstrap uses AU-PRO rebuilt on a 2000-threshold FPR grid; the grid error against exact must be ≤ 2×10⁻³ per category (checked and reported).

**Sensitivity analysis:** a two-level bootstrap that resamples categories as well as images, which is more conservative. It is reported alongside the primary result.

## H-01.5 Smallest effect of interest and decision rules

**SESOI δ = 2.0 AU-PRO points** (0.020).

Rationale: PatchCore reports a 0.2-point aggregate PRO change from 100 % to 1 % memory and calls it parity. A size-specific penalty of at least 10× that is large enough to change a deployment decision; smaller differences are what the field already treats as "comparable". δ is a judgement fixed before data, stated as such.

| Verdict | Rule |
|---|---|
| **Supported** | 95 % CI lower bound of D > 0, **and** D ≥ δ, **and** D > 0 on all 3 seeds |
| Reversed | the mirror-image condition (large defects lose more) |
| **Informative null (equivalence)** | the 90 % CI of D lies entirely inside (−δ, +δ): TOST at α = 0.05 |
| Detectable but small | the CI excludes 0 but the conditions for Supported fail |
| **Inconclusive** | anything else. Reported as inconclusive; **non-significance is never presented as equivalence** |

**Precision check before the full grid.** After the pilot, the expected CI half-width is estimated **from the arms' variability on the reference arm only** (image-bootstrap SD of bin AU-PRO). No comparative pilot outcomes are used for this. If the projected half-width exceeds δ even with all 15 categories, this is reported before spending the full-grid allocation, so you can decide whether the study can answer the question.

## H-01.6 Exploratory, descriptive only (no claims of mechanism or method)

- How compression changes the nearest-neighbour distance of normal test patches, and the score margin of S vs L regions (max score in the region minus the 99th percentile of good-image pixel scores).
- These are reported as descriptions. They motivate no method in this study.

## H-01.7 Abandon / stop

- If the primary result is an informative null or is inconclusive, the paper reports exactly that, with the CI.
- No further budgets, metrics or bins are added post hoc to find an effect.

Cost: provisional (COMPUTE_LEDGER). The measured pilot throughput replaces it before any full-grid approval.

Outcome: (pending)

---

## Reproduction targets (P-REPRO, separate setup, registered 2026-10-11)

P-REPRO uses PatchCore's own preprocessing: Resize 256 → CenterCrop 224, bilinear-and-floor masks, and metrics on the crop. Its only purpose is to check our implementation against published numbers; it never enters H-01.

| Protocol | Quantity | Published | Source | Tolerance |
|---|---|---|---|---|
| P-REPRO | PatchCore WRN-50, 10 % coreset, mean image AUROC | 99.2 (official script comment) / 99.1 (paper) | `sample_training.sh`; Roth et al. 2022 | ±0.5 pt |
| P-REPRO | mean pixel AUROC (224 crop) | 98.1 | same | ±0.3 pt |
| P-STUDY | PatchCore AU-PRO@0.3, official script, no crop | 92.7 (re-run by EfficientAD's authors) | Batzner et al. WACV 2024 | ±1.0 pt |
| P-REPRO | PaDiM-WR50-Rd550: detection AUROC / localisation AUROC / PRO | 95.3 / 97.5 / 92.1 | Defard et al. 2021, Tables (read 2026-10-11) | ±1.0 pt each |

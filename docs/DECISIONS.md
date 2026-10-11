# Decision log

Numbered, dated, with reasoning. Superseded decisions are marked, never deleted.

**D-001 (2026-10-11) Topic frozen; resource overrides.** The topic statement in
STATE.md is frozen. The researcher's instructions override the playbook's
resource assumptions:
- No GTX 1060 and no Kaggle.
- All GPU work runs on Colab under explicitly approved CU allocations.
- The ~300 CU balance is shared across projects and is not this project's budget.
- The laptop (8 CPUs, 14 GB RAM with ~4 GB free, Python 3.14 system / 3.12 venv) is for code, CPU tests, literature, and writing.

**D-002 (2026-10-11) Repository location.** The session directory
(`~/Paper/Anomaly Memory Compression`) was empty and not a checkout. The
remote was empty. As instructed, it was cloned to `~/Research/Anomaly-memory-compression/`.

**D-003 (2026-10-11) Dataset storage.**
- The verified compressed archive is persisted on Drive.
- Active work uses a locally extracted copy, re-staged per runtime (a 5.3 GB copy plus extract takes minutes).
- No unpacked Drive copy. It would double Drive use, and FUSE reads of ~5,000 PNGs are slower and less reliable than local disk.
- The publisher gives no checksum, so we record our own SHA-256 and label it as ours.

**D-004 (2026-10-11) Metric replica.** We use the official MVTec AD algorithm:
- every distinct score as a threshold;
- 8-connected ground-truth regions;
- FPR over all defect-free pixels of all test images;
- trapezoid to the FPR limit with interpolation, divided by the limit.

Reported at FPR 0.3 (MVTec AD convention) and 0.05 (MVTec AD 2 convention, more sensitive to small defects). Image and pixel AUROC are exact, with ties merged.

It is validated against the vendored official code (BSD-3) to ≤3e-8 on 200 randomized cases, the official toy example and analytic cases. The difference comes from the official code's float32 FPR.

Rejected: anomalib before v2.3 and RD4AD PRO variants (they normalise by the last FPR, not by the limit), and PatchCore's `anomaly_pro` column (anomalous images only).

**D-005 (2026-10-11) Two evaluation protocols, never mixed.**
- **P-REPRO**: PatchCore's own preprocessing.
  - Images and masks go through Resize 256 → CenterCrop 224.
  - The mask is resized bilinearly and floored, so only fully covered pixels stay anomalous (threshold 0.999).
  - Metrics are computed on the crop.
  - Used **only** to check our PatchCore reproduction against published PatchCore numbers.
- **P-STUDY**: no crop.
  - Maps are upsampled to native resolution and evaluated against native-resolution masks, as the official MVTec script requires.
  - This also preserves the native mask measurements the size analysis needs.
  - Every study claim uses P-STUDY.

Each protocol is a separate config with its own experiment identity. EfficientAD and Costanzino et al. report no-crop results, so P-STUDY is the comparable convention.

**D-006 (2026-10-11) Defect-size strata are pre-registered before any outcome.** The definitions are in REALITY_CHECK H-01. The strata use native masks only and are fixed by config before any comparative outcome is seen. The outcome-free profile may be consulted only to apply the pre-written merge rule.

**D-007 (2026-10-11) Baseline list.** See LITERATURE §2:
- trivial sanity baselines;
- random-selector control;
- official PatchCore (Apache-2.0) with its approximate greedy coreset;
- one normal-only density/coverage comparator (PaDiM or SPADE kNN, frozen at Phase 1 start).

ProCon is related work only: its author repo has no licence file (GitHub API, 2026-10-11).

**D-008 (2026-10-11) EfficientAD excluded from experiments.**
- There is no official code; github.com/nelson1425/EfficientAD is unofficial.
- Exact reproduction needs ImageNet twice: teacher distillation and the per-step penalty images.
- ImageNet is restricted and will not be downloaded, and substitutes do not reproduce the published numbers.

It is cited in related work with its published no-crop numbers.

**D-009 (2026-10-11; storage part SUPERSEDED by D-018) What gets stored.**
- **Not cached:** full backbone features. At P-STUDY resolution, train patches alone are ≈3.7 M × 1536 dims × 2 B ≈ 11 GB, while extraction is cheap compared with coreset selection.
- **Persisted per (category, selector, seed):** coreset index lists, which are tiny and define each bank given the features.
- **Persisted per test image:** raw patch-level score grids (the kNN distances before upsampling and smoothing), at e.g. 32×32 float32 ≈ 4 KB per image.
- **Rebuilt on CPU at evaluation:** native-resolution maps, by deterministic bilinear upsampling plus Gaussian σ=4.

This keeps raw predictions for free re-scoring at roughly 7 MB per run instead of GBs. Memory cost is reported in bytes (dtype × vectors × dims + index overhead) per D-012.

**D-010 (2026-10-11) Target venue: Pattern Recognition first, Neurocomputing as fallback.**
- **Pattern Recognition:** the scope covers computer vision and pattern-analysis methodology. It recently published memory-bank AD work (MMFNet, verified). Requirements: 20–35 pages, single column, double spaced (shop.elsevier.com).
- **Neurocomputing:** cheaper open access and a faster first decision (snippet only). Fit requires framing around learned representations.
- **Template:** elsarticle v3.5 (LPPL 1.3); there is no journal-specific template. The skeleton switches to numbered references (`elsarticle-num`), as PR papers use.
- **Cost route:** subscription, so no APC.
- **Still unverified:** JCR quartile and impact factor; PR's mandated reference style; exact declaration wording. To be checked in a normal browser before submission.

**D-011 (2026-10-11) Nested greedy coresets.**
- The official `ApproximateGreedyCoresetSampler` loop picks the argmax of the running min-distance each iteration, and its only dependence on the target count is when it stops.
- So for a fixed seed (projection weights + 10 start points) the first K picks of a 10 % run are exactly the K-point coreset (verified by reading `src/patchcore/sampler.py`, 2026-10-11).
- One selection per (category, seed) therefore yields every smaller budget.
- Phase 1 must confirm prefix equality with a test before any cost estimate relies on it.

**D-012 (2026-10-11) Budgets compared at matched bytes.**
- The ratio grid (0.1, 1, 5, 10 %) is provisional.
- Comparisons across selectors and methods are made at equal total memory bytes, including dtype, every bank and layer, and index overhead (`memory/accounting.py`).
- Ratios are reported alongside, never instead.

**D-013 (2026-10-11) Environment.**
- Lower-bound requirements, because Colab's preinstalled numpy, scipy and torch must not be upgraded.
- Every run records `pip freeze` in its manifest.
- Local development uses a Python 3.12 venv to match Colab's minor version.
- A pinned release lockfile is produced from the Colab environment of the final results.

**D-014 (2026-10-11) Acquisition route.** The tool resolves the link from the official downloads page on each run and falls back to the recorded URL only with a printed warning. The overview page's "fill in the form" is an open question for the researcher (DATA.md).

**D-015 (2026-10-11) Phase 0 runs no accelerator work.** Measuring backbone throughput is deferred to the approved pilot. All cost figures in COMPUTE_LEDGER are provisional until then.

**D-016 (2026-10-11, researcher's instruction) Topic frozen as an empirical study.**
- Frozen topic: "At fixed feature extraction and measured memory budgets, does memory-bank compression disproportionately reduce industrial anomaly segmentation performance on small defects?"
- The contribution is a controlled empirical study.
- The earlier "coverage-preserving correction" is **withdrawn**. Any later method needs separate evidence, a separate literature review and separate approval.
- H-02 is deleted. The mechanism analysis remains as descriptive, exploratory reporting only (REALITY_CHECK H-01.6).

**D-017 (2026-10-11) Density comparator: PaDiM (not SPADE).**
- **A different memory family.** PaDiM is a parametric, normal-only density memory: a per-position Gaussian whose footprint does not depend on the training-set size. It is therefore a genuinely different compression family from exemplar subsampling.
- **Its own byte knob.** Its random channel reduction (Rd100 vs Rd550 in the paper) gives explicit, measurable byte points to place on the same bytes-vs-size-stratified-AU-PRO plot.
- **Verified published numbers.** WR50-Rd550 reports detection AUROC 95.3 and localisation AUROC/PRO 97.5/92.1 (Defard et al., read 2026-10-11), which gives a reproduction check.
- **Why not SPADE.** SPADE is exemplar kNN over the full memory. That is already covered by our uncompressed PatchCore-feature reference, so it would add little. Its published numbers are also weaker (85.5 detection; 96.5/91.7 localisation).
- **Caveats.** There is no official PaDiM code, so we write a minimal re-implementation from the paper, tested on CPU, and label it as such. PaDiM assumes aligned objects; that is reported, not tuned around.
- **Role.** PaDiM is a comparator only. It does not enter the primary contrast, which stays within one fixed extractor.

**D-018 (2026-10-11) Feature caching and resumability (supersedes the storage part of D-009).**
- **Execution unit** = (category, protocol). One job per category:
  1. Extract features once (seed-independent: frozen backbone, no augmentation).
  2. Cache them on Colab local disk, keyed by `features/cache.py` (dataset hash, split hash, geometry, weights SHA, layers, aggregation, precision, code hash).
  3. Run every seed × selector × budget × scoring from that cache.
- **Persisted to Drive (atomically):**
  - the greedy coreset state every N picks (selected indices + running min-distance vector, ≤ 2 MB), so a long hazelnut selection resumes mid-run;
  - final coreset indices (tiny);
  - raw 32×32 score grids (≈4 KB/image);
  - per-arm manifests.
- **Not persisted by default:** full feature tensors. P-STUDY features are ≈15 GB (train) + ≈7 GB (test) at fp32, against minutes of re-extraction per category. They are copied to Drive only if you confirm the Drive space, and only within the approved allocation.
- **Reuse:** extraction once per category instead of once per arm × seed. With nested coresets (D-011), one greedy run per (category, seed) yields every budget. A resumed job skips completed (category, arm, seed) units after manifest validation.

**D-019 (2026-10-11) Memory accounting.** See REALITY_CHECK H-01.1:
- fp32 vectors plus the measured serialized index overhead;
- the selection-time projection is excluded but reported;
- PaDiM is counted from its stored mean and inverse-covariance arrays;
- backbone weights are excluded from per-arm bytes.

**D-020 (2026-10-11) Statistics.**
- Paired, stratified image bootstrap. The same resampled images apply to every arm and seed; categories are fixed strata; seeds are averaged, with a sign-consistency requirement.
- Single primary test.
- SESOI δ = 2.0 AU-PRO points; equivalence by TOST using the 90 % CI.
- Explicit "inconclusive" category: non-significance is never reported as equivalence.
- Implemented in `eval/stats.py` and tested on synthetic data.

**D-021 (2026-10-11) Size unit.**
- Primary: 8-connected component at native resolution, with S/M/L bins at 0.1 % and 1 % of image pixels. The S boundary equals one feature cell at 256 px.
- Multi-defect images are handled through the region filter.
- Secondary image-level bins use the largest component, plus a mixed-image exclusion analysis.

**D-022 (2026-10-11) Pilot outcome blinding.** No size-stratified comparison is computed from pilot outputs. Only throughput, resume reliability, manifest validity and pipeline sanity are inspected.

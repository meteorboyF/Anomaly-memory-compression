# Compute ledger

**Phase 0 used 0 accelerator units.** All Phase 0 work runs on the laptop CPU or on Colab **CPU** cells executed by the researcher.

Rules:

- Every accelerator batch needs an approved allocation in `configs/control/allocations.yaml`, with these fields:
  - CU ceiling
  - GPU type
  - CU/hour rate as displayed in the researcher's Colab session
  - conservative wall-clock limit
- `budget.preflight` refuses anything else.
- The wall-clock guard is approximate and is **not a CU meter**.
- After each batch: reconcile against the Colab balance, record the batch below, and request the next allocation. Batches are never launched automatically.
- The ~300 CU account balance is shared with other projects. It is not this project's budget.

**No GPU-hour → CU conversion is assumed anywhere.** Costs are given in GPU wall-hours and turned into CU only with the rate the researcher reads off their session.

## Batch log

| Date | Allocation | Config(s) | GPU | Wall h | Start → end CU balance | CU spent | What it bought |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | 0 | Phase 0 (CPU only) |

## Provisional grid costing (2026-10-11): UNMEASURED

Every number below is an engineering estimate from operation counts. None is a measurement. The pilot (H-00) replaces them before any later approval. Uncertainty is about ×0.3–×3 per line.

Basis of the estimates:

- **Patch counts.** At P-STUDY (Resize 256, no crop) PatchCore yields 32×32 = 1,024 patches per image. Train totals are ≈3.7 M patches; the largest category, hazelnut, has ≈0.40 M.
- **Coreset cost.** The approximate greedy coreset costs about K·N·d multiply-adds per category (K picks, N patches, d = 128 projected dims), and is memory-bound on a GPU.
  - K = 10 % for all categories: Σ 0.1·N_c² · 128 · 2 ≈ 2×10¹³ FLOP.
  - At an assumed effective 2–4 TFLOP/s on a T4, that is about 1.5–3 h per seed.
- **Nested prefixes (DECISIONS D-011).** One 10 % run per seed yields the 0.1 / 1 / 5 % coresets as prefixes, so smaller budgets cost nothing extra.
- **Feature extraction.** WRN-50 forward on 5,354 images is minutes. Decoding the PNGs on Colab's 2 vCPUs likely dominates: ≈10–20 min per full pass.
- **kNN scoring.** Test patches 1.7 M × bank ≤ 0.4 M × 1,024 dims: minutes per arm. The uncompressed reference is the costliest arm, still ≲ 1 h total.
- **Evaluation.** CPU only. Native-resolution maps are rebuilt from stored score grids (D-009).

| Line | Content | T4 wall-h (est.) |
|---|---|---|
| G0 pilot (H-00) | 2 categories × 1 seed, all arms, resume test, setup + staging | 0.75–1.5 |
| G1a baseline reproduction, P-REPRO | 15 categories × 3 seeds, 10 % greedy coreset, 224 crop | 2–5 |
| G1b baseline under P-STUDY | 15 categories × 3 seeds, greedy to 10 % (all budgets nested) + uncompressed reference | 5–10 |
| G1c selector control + density comparator | random selector (cheap) + PaDiM or SPADE, 3 seeds | 1–2 |
| G2 sensitivity checks | e.g. projection dim, smoothing σ, second layer set: 2–3 rows × 3 seeds, all reusing extraction | 3–6 |
| Re-runs, staging, idle (setup per session ≈15 min) | — | 2–3 |
| **Subtotal** | | **14–27** |
| **× 1.5 contingency** | | **21–41 T4 wall-h** |
| Cold-clone reproduction test (pre-submission) | smallest complete result: 1 seed, 1–2 categories + all figures | 1–2 |

This is well below the earlier unmeasured brainstorm figure of 45–90 T4-h. The reasons are nested coresets and not caching features (DECISIONS D-009/D-011). That figure is superseded and was never an approved target.

A100 is not planned. A justified comparator (H-02) would be costed separately, only if H-01 passes.

**Storage (Drive).**

| Item | Size |
|---|---|
| Archive | 5.26 GB |
| Coreset indices | ≪ 100 MB |
| Raw score grids | ≈7 MB per (arm, seed) run; ≈1 GB for the whole grid |
| Logs and manifests | ≪ 1 GB |
| **Total** | **< 8 GB** |

## Initial pilot allowance: PROPOSAL (not approved)

| Item | Proposal |
|---|---|
| Single question | Does the full pipeline run on Colab and resume after interruption, and what are the measured per-category costs (images/s, coreset iterations/s, peak VRAM, bank bytes)? |
| Scope | Categories toothbrush (smallest) and hazelnut (largest train set, cost upper bound). Seed 0. Greedy coreset to 10 % plus random selector plus uncompressed reference. One deliberate interrupt-and-resume. Never a 15-category grid |
| GPU | **T4**, the cheapest adequate option. WRN-50 inference in fp32 fits in 16 GB, and the coreset is memory-bound, so A100 speed would mostly be wasted. L4 is reconsidered only if pilot throughput shows T4 cost per completed job is higher |
| Expected time | 0.75–1.5 h wall, including ≈15 min of setup, Drive staging and extraction while the GPU is attached (the runtime switch forces a re-stage) |
| Wall-clock guard | **1.5 h**, with a checkpoint 5 min before the limit |
| CU estimate | 1.5 h × *your displayed T4 rate*. **I need the CU/hour Colab shows for a T4 runtime** (or your balance before and after) to set the CU ceiling. I do not assume a rate |
| Outputs | Coreset index lists, raw score grids, manifests, throughput table, a resume-test record, all on Drive. The measured throughput replaces the estimates above. Artifacts are reused in G1b only if their per-category experiment identity matches (Phase 1 keys artifacts per category for this reason); otherwise they are kept as pilot-only records |
| Stop condition | Both categories complete with verified manifests, **or** the guard is reached, **or** any failure that is not an ordinary code bug. Then disconnect the runtime, reconcile CU, and report |
| Prerequisite | Phase 1 code (extraction, coreset, scoring) written and `--smoke`-tested on laptop CPU first. Not started before gate approval |

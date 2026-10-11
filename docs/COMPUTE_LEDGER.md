# Compute ledger

**Accelerator units used so far: 0.** Phase 0 runs only on the laptop CPU and on Colab **CPU** cells that you execute.

Rules:

- **Allocations.** Every accelerator batch needs an allocation that you approved in chat. It is recorded in `configs/control/allocations.yaml` with:
  - the CU ceiling;
  - the GPU type;
  - the CU/h rate **as displayed in your Colab session**;
  - a conservative wall-clock limit.
- **Enforcement.** `budget.preflight` refuses anything else. The wall-clock guard is approximate and **is not a CU meter**.
- **After each batch:** reconcile against the balance you observe, log the batch below, and stop. The next allocation is requested, never assumed.
- **Shared balance.** The ~300 CU balance is shared across your research. It is not this project's budget.
- **No conversion is assumed.** No GPU-hour → CU conversion is used anywhere. CU figures come only from your displayed rate or observed balance changes.

## Batch log

| Date | Allocation | Config(s) | GPU | Wall h | CU balance start → end | CU spent | What it bought |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | 0 | Phase 0 (CPU only) |

## Correction to the earlier estimate (2026-10-11)

The first provisional costing gave **21–41 T4-h**. Its dominant line (greedy coreset, "1.5–3 h per seed") was an **arithmetic error**.

- The operation count (≈2×10¹³ FLOP for every category at 10 %) is right.
- At an effective 2–4 TFLOP/s that is seconds of compute, not hours.
- Real coreset time is dominated by per-iteration overhead of the selection loop: ≈40 k iterations for hazelnut, perhaps 1–5 ms each. That is **minutes per (category, seed)**.

The 21–41 h figure is withdrawn. The estimate below replaces it. It is still **unmeasured**, and the pilot exists to measure it.

## How the design avoids repeated computation (D-011, D-018)

| Mechanism | Without it | With it |
|---|---|---|
| Features cached per (category, protocol) on local disk, keyed by cache identity | Backbone re-run for each seed × selector × budget × arm: ≈3 seeds × 2 selectors × 4 budgets ≈ 24× per category | **1×** per category per protocol. Features are seed-independent (frozen backbone, no augmentation) |
| Nested greedy coresets (official sampler: the 10 % run's first K picks = K-point coreset) | One selection per budget (10 + 1 + 0.1 %) | **One** selection per (category, seed); smaller budgets are prefixes |
| Category-wise jobs with per-unit manifests | A crash loses the whole grid run | A crash loses at most the in-progress (category, arm, seed) unit; completed units are skipped after validation |
| Greedy state checkpointed to Drive every N picks (≤2 MB) | A lost runtime restarts selection from zero | Resume mid-selection |
| Raw 32×32 score grids persisted; maps rebuilt and evaluated on a **CPU** runtime | Re-score on GPU for every metric change | GPU never used for evaluation; every re-scoring is free |
| Evaluation after disconnecting the GPU | Native-resolution evaluation (≈1 min/category, ~8.5 GB RAM) bills GPU time | Runs on a CPU runtime |

## Provisional costing (UNMEASURED; uncertainty ≈ ×0.3–×3 per line)

**Unit assumptions.** All of these are measured by the pilot:

- **Image decode + resize.** Colab's 2 vCPUs, 700–1024 px PNGs: ≈20–40 img/s. That is ≈3–5 min per full pass of 5,354 images and dominates extraction.
- **WRN-50 forward at 256 px, fp32, T4.** Faster than decoding, so it does not set the pace.
- **Greedy selection.** Hazelnut is the largest category: 391 × 1024 ≈ 0.40 M patches, so a 10 % selection is ≈40 k iterations. At 1–5 ms/iteration that is ≈1–4 min per (category, seed); smaller for the other categories.
- **Exact kNN scoring.** Test patches × bank × 1024 dims: ≈10¹⁴ FLOP for the largest uncompressed arm, i.e. seconds to a minute per arm.
- **Session overhead.** About 15–20 min per GPU session: re-staging the 5.3 GB archive from Drive and extracting it, which the runtime switch forces.

| Line | Content | T4 wall-h (est.) |
|---|---|---|
| G0 pilot (H-00) | 2 categories, seed 0, all arms, resume test, one session | **0.5–1.0** |
| G1a reproduction, P-REPRO | 15 categories × 3 seeds PatchCore 10 % + PaDiM-Rd550 | 1.5–3 |
| G1b study, P-STUDY | 15 categories × 3 seeds: reference + greedy (nested 10/1/0.1 %) + random at matched bytes; PaDiM Rd100/Rd550 | 3–6 |
| Session overhead | ≈5–7 sessions × 15–20 min | 1.5–2.5 |
| Re-runs after fixes | — | 1–2 |
| **Subtotal** | | **7.5–14.5** |
| **× 1.5 contingency** | | **≈11–22 T4 wall-h** |
| Cold-clone reproduction test (pre-submission) | 1 seed, 1–2 categories + all figures | 0.5–1 |

Evaluation, bootstrap statistics, figures and tables run on CPU (laptop or a Colab CPU runtime) and are not in this table.

Storage on Drive:

| Item | Size |
|---|---|
| Archive | 5.26 GB |
| Coreset indices and checkpoints | < 0.2 GB |
| Score grids | ≈7 MB per (arm, seed, protocol) run; < 2 GB overall |
| Manifests and logs | < 0.5 GB |
| **Total** | **< 8 GB** |

Optional feature caching on Drive would add ≈22 GB (P-STUDY) and is **not planned** unless you confirm the space (D-018).

## Pilot allowance: PROPOSAL (not approved)

| Item | Proposal |
|---|---|
| Purpose | **Execution, resume reliability, measured cost.** Not hypothesis testing. No size-stratified comparison is computed from pilot outputs (D-022) |
| Categories | **hazelnut**: the largest training set (391 images → ≈0.40 M patches), so it sets the upper bound on bank memory, greedy iterations, uncompressed kNN cost and VRAM.<br>**screw**: 320 training images (second-largest bank); the largest native evaluation volume (160 test images × 1024²) for the CPU-side memory check; grayscale (exercises the 1→3-channel path); many thin, small defects (exercises native-resolution mask handling) |
| Arms | uncompressed reference; greedy to 10 % (prefixes 1 % and 0.1 %); random at matched bytes; PaDiM-Rd100. Seed 0 only |
| Resume test | Kill the hazelnut greedy job once, mid-selection, resume, and verify byte-identical indices. Also verify prefix equality (D-011) |
| GPU | **T4**, the cheapest adequate option: fp32 WRN-50 inference and a ≤1.6 GB bank fit in 16 GB. The work is overhead- or memory-bound, so A100 speed would mostly be wasted. After the pilot I compare cost per completed (category, seed) unit on T4 vs L4 using measured throughput and your displayed rates |
| Expected wall time | 0.5–1.0 h, including ≈15–20 min of staging while the GPU is attached |
| Wall-clock guard | **1.0 h**, with a checkpoint 5 min before the limit |
| CU cap | **1.0 h × the T4 CU/h rate shown in your session**, or your balance before and after. I have no rate yet, so no CU number is proposed |
| Outputs | Measured: images/s, greedy iterations/s, kNN queries/s, peak VRAM and RAM, bank bytes per arm, staging time. Plus manifests, coreset indices, score grids, resume record. The throughput replaces every estimate above. Artifacts are reused in G1b only if their per-category identity matches |
| Stop | Both categories verified, **or** guard reached, **or** any non-routine failure. Then verify, disconnect, reconcile CU, report |
| Prerequisites | (1) Phase 0 gate approved; (2) Phase 1 code (extraction, coreset, scoring, PaDiM) written and `--smoke`-tested on laptop CPU; (3) a CU cap from your observed rate |

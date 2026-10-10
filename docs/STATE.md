# STATE — single source of truth (update every session)

_Last updated: 2026-10-11, end of session 1._

## Frozen topic (D-001)

- **Problem:** compressing the normal-feature memory in industrial anomaly detection may preserve aggregate benchmark scores while disproportionately reducing sensitivity to small defects.
- **Hypothesis:** at matched memory budgets, compression changes how well normal-feature neighbourhoods are covered, and this disproportionately affects small-defect sensitivity. A normal-data-only coverage strategy may improve the trade-off.
- **Intended contribution:** a controlled study of memory compression versus detection and localisation conditioned on defect area. A coverage-preserving correction follows only if experiments support the mechanism.
- **Benchmark:** original MVTec AD, all 15 categories, official splits, existing pixel masks.

**Phase 0 novelty verdict: CROWDED, rescoped.** See LITERATURE §1. The diagnostic study is the contribution. The correction is conditional and must beat HR-Pro-style residual coverage.

## Phase: 0 (literature + feasibility). Gate NOT yet approved.

Accelerator use: **0 CU**. `configs/control/gates.yaml` has all phases unapproved. `allocations.yaml` is empty, so every GPU tool refuses.

### Done (verified on the laptop)

- [x] Playbook read, including the brainstorm notes. The playbook's resource assumptions are overridden (D-001).
- [x] Repository skeleton and harness, with 75 CPU tests passing:
  - strict configs, manifests with `complete` written last;
  - experiment identity from config + scientific code;
  - budget preflight and wall-clock guard;
  - acquisition tool, profile, evaluator, trivial baselines;
  - Colab driver and control CLI, notebook generator;
  - pre-commit guard and CI workflow.
- [x] Acquisition live path checked against the real publisher: link resolved from the downloads page; size and ETag match. No download was run locally.
- [x] Metric replica matches MVTec's official evaluation code (max deviation 3e-8). This is a laptop run from a dirty tree and is not citable; the citable run is Colab Cell 3.
- [x] Literature protocol: about 130 logged queries across two passes, a 15-row closest-paper matrix, and personal verification of the decisive papers.
- [x] Pre-registration H-01 (strata, metrics, tests, falsification, mechanism check) and pilot proposal H-00.
- [x] Manuscript skeleton on elsarticle v3.5 compiles; Related Work drafted.

### Pending: needs the researcher

1. Run Colab Cells 1–3 on a **CPU** runtime (docs/COLAB.md) and send the output.
2. Decide on MVTec's "fill in the form" (DATA.md, access question).
3. Tell me the **CU/hour Colab displays for a T4** (or the balance before and after a batch), so the pilot's CU ceiling can be set without assuming a rate.
4. Approve or reject the Phase 0 gate and the pilot allowance (COMPUTE_LEDGER).

### Open Phase 0 items (agent side)

- Venue verification pass (in progress at the time of writing; see D-010).
- Full text of Tu 2026 and HR-Pro: both are open access, but our fetchers could not read IEEE Xplore. The researcher could download the two PDFs into `~/Research/papers/` for me to read.
- Choose the density comparator (PaDiM vs SPADE) by reading their code on CPU at the start of Phase 1.

## Exact next commands

Colab, CPU runtime:

```
Cell 1  (setup)  ->  Cell 2  (acquire_data --config acquire_mvtec_ad)
Cell 3  (metric_selfcheck, profile_data, evaluator_sanity, evaluator_sanity_native)
Cell 11 (status + verify), then Runtime > Disconnect and delete runtime
```

Laptop, after the Colab run (to mirror small results into the repo for the paper), with Drive synced or the manifests copied locally:

```
.venv/bin/python tools/sync_results.py --from <path to Drive artifacts/manifests>
.venv/bin/python scripts/make_tables.py && .venv/bin/python scripts/make_figures.py
```

## What the units bought this week

Nothing: no units were spent. That is by design for Phase 0.

## Next session's single most important question

Does the outcome-free profile show enough small (<0.1 %) and large (≥1 %) defect regions per category for H-01's pre-registered strata to be testable on MVTec AD alone? If not, apply the merge rule now, before any model output exists.

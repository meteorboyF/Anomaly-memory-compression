# Literature: related-work matrix, search log, novelty verdict

Protocol: `03_LITERATURE_AND_NOVELTY.md` (live search only, every citation
resolved). Phase 0 sweep run **2026-10-11** by three parallel search passes
(A: memory compression × defect size; B: evaluation protocol & baselines;
C: venues), followed by my own verification of every item that decides the
verdict (marked ✔ below). Raw search records of A and B follow in full
(Appendix A/B); C is in `docs/DECISIONS.md` D-010 and §Venues below.

Next delta sweeps: at the Phase 1 → 2 boundary, and **~2026-11-08** targeted
at the Chae group (ProCon / memory-composition line) and "coreset AND defect
size", and within 2 weeks of submission.

## 1. Novelty verdict (Phase 0): **CROWDED — rescoped**

The diagnostic claim (memory compression × defect-size sensitivity at matched
bytes, category-controlled) has **no direct prior measurement** in anything we
found; but every ingredient exists separately, and the proposed correction
direction is already occupied. Per the playbook this is *Crowded*: publishable
only if the controlled evaluation itself is the contribution. Rescoped claim:

> **Rescoped contribution.** A controlled, pre-registered measurement of
> whether memory-bank compression of training-free patch-memory detectors
> (PatchCore-style) changes detection and localisation of *small* defects
> differently from large ones on MVTec AD, at matched memory **bytes**, across
> selectors (greedy k-centre coreset vs random vs a density/coverage
> comparator), with category controls, ≥3 paired seeds, and the official
> AU-PRO. A correction is pursued **only** if the effect exists, and must then
> beat HR-Pro-style residual coverage, not just PatchCore.

What the paper may NOT claim: a new size-robustness metric (Costanzino et al.
2025 already defines quartile AU-PRO and ρ); that compression is known to be
free/harmful (contested, measured only in aggregate); a novel coverage
correction (HR-Pro, CPD-PatchCore, CleanCon/risk-aware coverage, SuperADD).

### Closest papers and the delta (one sentence each)

| Paper | ✔ | What it shows | Delta to us |
|---|---|---|---|
| Roth et al., PatchCore, CVPR 2022, doi:10.1109/CVPR52688.2022.01392 | ✔ Crossref | 1 % / 10 % / 100 % coreset give ≈ equal mean image AUROC, pixel AUROC, PRO; subsampler comparison aggregate-only | We condition its own budget axis on defect area |
| Kamiya et al., ASO PatchCore, VISAPP 2026, doi:10.5220/0014445100004084 | ✔ Crossref | ≈86 % memory reduction vs 10 % PatchCore with "comparable" aggregate metrics | Prime target: we test whether that parity holds for the smallest-defect strata |
| Chae et al., ProCon, arXiv 2607.04894 (v1, 2026-07-06) | ✔ arXiv | 1/5/10 % budget sweep and seed-perturbed banks; aggregate P-AP saturates at 5 %; no size conditioning | We condition budget and seed variation on defect area |
| Costanzino et al., IEEE Access 2025, doi:10.1109/ACCESS.2025.3582900 | ✔ full text read | Cumulative size-quartile AU-PRO@30 %/@5 % and robustness ρ; PatchCore at its **default** memory only; states MVTec AD is comparatively size-stable | We cross their size protocol with memory budget and selector; their MVTec finding is our main null-result risk |
| Chae et al., arXiv 2608.23295 (2026-08-24) | ✔ arXiv | Selector comparison (random/medoid/farthest-first) at matched K under contamination | Same matched-K methodology; outcome is contamination, not defect size |
| Feng et al., HR-Pro, IEEE Access 2026, doi:10.1109/ACCESS.2026.3725847 | ✔ Crossref; full text NOT read | Residual normal patches restore coverage in compressed prototype memory | Pre-empts the correction; must be read in full and compared against if Phase 2 happens |
| Tu, IEEE Access 2026, doi:10.1109/ACCESS.2026.3733273 | ✔ Crossref; full text NOT read | Greedy coreset degrades pixel-level results on MVTec AD 2 (few-shot) | If it stratifies by size, the gap narrows — **open gate item** |

Protocol-search correction: pass B reported that no paper breaks MVTec AD
results down by defect size. That is **wrong**; Costanzino et al. do (verified
in the full text, Sec. IV-A.2 and Tab. 2). Pass A's reading is the correct one.

### Risks recorded with the verdict
1. **Null result on MVTec AD** (Costanzino: size-stable; PatchCore: 1 % ≈ 100 %).
   Pre-registered response: a properly powered null ("compression to X bytes is
   size-neutral within ±δ on MVTec AD") is reported as the finding, and the
   correction is not built (REALITY_CHECK H-01 abandon clause).
2. **Scoop**: the Chae group publishes matched-budget memory studies monthly.
   Mitigation: the delta sweep on ~2026-11-08 and at each milestone.
3. **Single benchmark**: MVTec AD defects are mostly 0.1–10 % of the image.
   A second dataset (e.g. VisA) would strengthen a size claim but must pass
   independent access/licence/size/ground-truth/baseline verification first;
   nothing is added silently.

## 2. Baseline list (from the matrix; DECISIONS.md D-007)

| Role | Method | Status |
|---|---|---|
| Evaluator sanity | constant, random, oracle-mask | implemented (CPU, Phase 0) |
| Selector control | random normal-memory subsampling at matched bytes | Phase 1 |
| Published standard | PatchCore, **official code** (Apache-2.0), approx. greedy coreset, WRN-50 L2+L3 | Phase 1 reproduction target |
| Normal-only density/coverage comparator | PaDiM (Gaussian per position; published 95.3/97.5/92.1) **or** SPADE kNN (uncompressed memory). Choice frozen at Phase 1 start after a CPU code read; both have no official code, so a minimal, tested re-implementation is required and labelled as such | to decide (gate item) |
| Strongest training-free memory comparator | ProCon — **no licence file** in the author repo, so code cannot be reused; cite its numbers, re-implementation only if justified | related work |
| Distillation comparator | EfficientAD — **excluded from experiments**: no official code; exact reproduction needs ImageNet for teacher distillation and the per-step penalty; Imagenette substitutes do not reproduce (anomalib 98.2/97.5 vs 98.8/99.1). Cite its published no-crop numbers | related work |

## 3. Venues (pass C, rerun after a network failure, 2026-10-11)

Recommendation: **Pattern Recognition first, Neurocomputing as fallback** (DECISIONS D-010).
Anchors verified by me on Crossref:
- MMFNet: Pattern Recognition 172, art. 112581 (2026), doi:10.1016/j.patcog.2025.112581.
- MP-DRA: Neurocomputing 655, art. 131427 (2025), doi:10.1016/j.neucom.2025.131427.

SJR 2025 Q1 for both journals and the review-speed figures come from search snippets only, because Scimago and ScienceDirect returned 403. **JCR quartile and impact factor are NOT verified.** SJR Q1 is not JCR Q1.
APCs are from Elsevier's official price list (05-Oct-2026): PR USD 3,120, Neurocomputing USD 2,660. Both journals are hybrid; the subscription route costs nothing.

Newly surfaced in the venue scan, to read in full in the Phase 1 delta sweep:
- BAMB (Neurocomputing 708, art. 135250, doi:10.1016/j.neucom.2026.135250): "boundary-aware coreset selection". No abstract was retrievable.
- Learnable product quantization for AD (Neurocomputing 582, art. 127532, doi:10.1016/j.neucom.2024.127532).
- "DA-Core" density-aware coreset: mentioned in a search snippet, not yet resolved.

---

## Appendix A — search pass A (memory compression × defect size), 2026-10-11, full record

### Phase-0 novelty search, scope A: memory-bank / coreset compression vs defect size

Date of search: 2026-10-11. Every paper listed below was resolved today: the arXiv abs/API record was fetched, or the DOI was resolved through doi.org (a 302 to the publisher), with metadata taken from the Semantic Scholar Graph API. Full text was read (PDF via `pdftotext`) for PatchCore, ProCon, ASO PatchCore, What-Memory-Composition, What-Remains-Normal, Learning-to-be-a-Transformer (Tiny-defect metrics), AUPIMO (size appendix), SubtleDC, and Lite PatchCore (grep-level). For the IEEE Access / SPIE / MDPI papers I could not get the full text: IEEE Xplore and the CVF CVPR-2022 PDF returned 403 or an empty page to the fetcher. For those, **only the abstract (S2) was read**, and this is flagged in each row.

Topic under test: *At matched memory budgets, PatchCore-style memory compression keeps aggregate MVTec AD metrics (I-AUROC / P-AUROC / AUPRO) but disproportionately hurts SMALL-defect sensitivity. A normal-data-only, coverage-preserving selection may fix the trade-off.*

---

#### 1. SEARCH LOG

All queries were run on 2026-10-11. "n relevant" counts hits that deal with memory/coreset compression or defect-size-conditioned evaluation.

| # | date | engine | query | n relevant hits | notable |
|---|---|---|---|---|---|
| 1 | 2026-10-11 | arXiv abs fetch | 2607.04894 (ProCon) | 1 | target paper; code jw-chae/Procon |
| 2 | 2026-10-11 | arXiv abs + PDF | 2106.08265 (PatchCore) | 1 | full PDF read via pdftotext |
| 3 | 2026-10-11 | WebSearch | PatchCore coreset subsampling ratio small defects | 3 | 2608.17775 HITL memory correction; MDPI dynamic-scaling PatchCore; 2307.10792 |
| 4 | 2026-10-11 | WebSearch | memory bank compression anomaly detection small defects | 3 | 2608.22082 contamination-aware memory; 2403.04932 tiled ensemble |
| 5 | 2026-10-11 | GitHub raw | amazon-research/patchcore-inspection sampler.py + README | 1 | projection dim 128, 10 starting points, Apache-2.0 |
| 6 | 2026-10-11 | GitHub API | jw-chae/Procon repo + contents | 1 | **no licence file**; created 2026-07-06, last push 2026-07-25 |
| 7 | 2026-10-11 | WebSearch | defect size stratified evaluation MVTec AD small anomalies detection performance by anomaly area | 3 | AUPIMO size appendix; 2604.07097 |
| 8 | 2026-10-11 | WebSearch | coreset selection anomaly detection memory efficient PatchCore alternative 2025 | 5 | **ASO PatchCore (VISAPP 2026)**; **2608.23295**; LUMIN; MECAD |
| 9 | 2026-10-11 | WebSearch | PatchCore memory bank size effect anomaly localization defect size analysis | 2 | Attention-driven explainable PatchCore (edge); ProCon |
| 10 | 2026-10-11 | WebSearch | AUPRO bias large defects size-aware metric anomaly segmentation small defects | 2 | AUPIMO; rwAP (region-weighted AP) |
| 11 | 2026-10-11 | arXiv abs/PDF | 2608.23295, 2608.17775, 2608.22082 | 3 | Chae et al. memory-composition study |
| 12 | 2026-10-11 | SciTePress PDF | ASO PatchCore 144451.pdf | 1 | full text read; DOI 10.5220/0014445100004084 |
| 13 | 2026-10-11 | arXiv API | au:Joongwon_Chae | 4 | ProCon, 2608.23295, **2608.23299 What Remains Normal?**, StructCore, GCR |
| 14 | 2026-10-11 | arXiv API | abs:coreset AND abs:anomaly AND abs:memory | 9 | ContCore 2608.15277, CADIC, SoftPatch(+), FAPM, edge CL |
| 15 | 2026-10-11 | arXiv API | abs:"memory bank" AND abs:anomaly AND abs:compression | 1 | LUMIN |
| 16 | 2026-10-11 | arXiv API | abs:"defect size" AND abs:anomaly | 1 | **2407.04092 (size-robustness metric ρ)** |
| 17 | 2026-10-11 | arXiv API | abs:"small defects" AND abs:"anomaly detection" AND abs:memory | 0 | — |
| 18 | 2026-10-11 | arXiv API | abs:"memory bank" AND abs:anomaly AND abs:efficient AND abs:patch | 2 | SoftPatch+, DINOv3 AR |
| 19 | 2026-10-11 | arXiv API | abs:"small anomalies" AND abs:"anomaly detection" AND abs:industrial | 0 | (HarmoniAD, Pyramid-Mamba: not memory) |
| 20 | 2026-10-11 | arXiv API | abs:PatchCore AND abs:subsampling | 1 | Mahalanobis PatchCore 2605.27748 |
| 21 | 2026-10-11 | arXiv API | abs:PatchCore AND abs:coreset AND abs:ratio | 0 | — |
| 22 | 2026-10-11 | arXiv API | abs:"anomaly size" AND abs:anomaly | 0 | (MSFlow only mentions size) |
| 23 | 2026-10-11 | arXiv API | abs:"defect area" AND abs:anomaly | 0 | Real-IAD and others; nothing on compression |
| 24 | 2026-10-11 | arXiv API | abs:"region size" AND abs:anomaly AND abs:segmentation | 0 | — |
| 25 | 2026-10-11 | arXiv API | abs:"memory-efficient" AND abs:"anomaly detection" AND abs:industrial | 1 | on-device CL PatchCore |
| 26 | 2026-10-11 | arXiv API | abs:"product quantization" AND abs:anomaly | 1 | **PatchCore-Lite 2603.20288** |
| 27 | 2026-10-11 | arXiv API | abs:PatchCore AND abs:quantization | 1 | PatchCore-Lite |
| 28 | 2026-10-11 | arXiv API | abs:"tiny defects" AND abs:anomaly | 0 | — |
| 29 | 2026-10-11 | arXiv API | abs:PatchCore AND abs:memory AND abs:reduce | 2 | Mahalanobis PatchCore; tiled ensemble |
| 30 | 2026-10-11 | arXiv API id_list | 2603.20288, 2605.27748, 2608.15277, 2605.24251, 2512.13497, 2609.04775, 2211.07381, 2312.03804, 2403.04932, 2401.01984, 2604.07097 | 8 | abstracts resolved |
| 31 | 2026-10-11 | S2 Graph API | citations of arXiv:2106.08265 (1,941 returned) filtered by coreset/memory/compress/size/efficient/small/tiny | ~40 | ASO PatchCore, HR-Pro, PatchCore-Q, Lite PatchCore, CPD-PatchCore, Memory Pollution, MAD-Flow, Lehr 2024 size-limit paper, FS on MVTec AD 2 |
| 32 | 2026-10-11 | S2 Graph API | paper lookups: Lehr 2024, IConSCEPT 2025, PatchCore++, PatchCore-Q, Lite PatchCore, LPQ Neurocomputing 2024, CPD-PatchCore, MAD-Flow | 8 | abstracts read |
| 33 | 2026-10-11 | WebSearch | "coreset" "small defects" PatchCore sensitivity memory reduction analysis | 1 | nothing new |
| 34 | 2026-10-11 | WebSearch | anomaly detection performance as function of defect size MVTec AD VisA analysis small anomalies missed | 3 | 2407.04092; AUPIMO; EfficientAD |
| 35 | 2026-10-11 | WebSearch | k-center greedy coreset anomaly detection analysis coverage radius normal features | 1 | BMVC 2025 learnable coreset (zero-shot; out of scope) |
| 36 | 2026-10-11 | WebSearch | memory bank subsampling anomaly detection density-aware coreset outperforms greedy coreset 2025 2026 | 2 | "DA-Core" hit was time-series (2509.12650), not image |
| 37 | 2026-10-11 | arXiv API id_list | 2407.04092, 2307.10792, 2609.03406, 2509.12650, 2501.12295, 2307.03243, 2403.14233, 2501.09579 | 3 | 2407.04092 read in full |
| 38 | 2026-10-11 | arXiv PDF | 2407.04092v3 full text | 1 | quartile AUPRO, ρ metric; MVTec "stable across sizes" |
| 39 | 2026-10-11 | arXiv PDF | 2401.01984v5 (AUPIMO) size appendix | 1 | MVTec region sizes 1e-3..1e-1 |
| 40 | 2026-10-11 | WebSearch | "memory budget" anomaly detection "defect size" OR "small defects" coreset ratio localization study | 2 | ProCon; Mahalanobis PatchCore |
| 41 | 2026-10-11 | WebSearch | coverage-preserving coreset memory bank anomaly detection rare normal patterns under-represented | 2 | 2608.23295; ContCore |
| 42 | 2026-10-11 | WebSearch | arXiv 2026 PatchCore memory bank pruning compression benchmark sensitivity analysis aggregate metrics hide | 1 | 2604.06435 continual edge benchmark |
| 43 | 2026-10-11 | WebSearch | "sPRO" OR "size-aware" anomaly localization metric small regions MVTec evaluation 2025 | 1 | sPRO (MVTec LOCO) only |
| 44 | 2026-10-11 | S2 search API | coreset anomaly detection memory bank small defects / PatchCore coreset sampling ratio / defect size anomaly segmentation evaluation small anomalies | — | **failed (HTTP 429 rate limit after retries)**; covered by arXiv API and WebSearch instead |
| 45 | 2026-10-11 | S2 search API | memory bank size anomaly detection defect size | 4 | Survey on 3D AD regarding defect size (IEEE Access 2025); distribution-aware memory refinement (IEEE Access 2026) |
| 46 | 2026-10-11 | S2 search API | memory-efficient PatchCore | 5 | **HR-Pro (IEEE Access 2026)**; ViT-Core+; FR-PatchCore |
| 47 | 2026-10-11 | arXiv API id_list | 2604.06435, 2605.14808, 2505.07119, 2504.02775, 2510.15602, 2505.19750, 2511.08634, 2603.02974 | 4 | SuperADD "improved memory-bank subsampling for coverage" |
| 48 | 2026-10-11 | arXiv API id_list | 2405.14529, 2206.04325, 2211.12634, 2301.12082, 2205.00908, 2412.20870, 2303.14535, 2503.21622 | 0 direct | AnomalyDINO, CFA, PNI, GraphCore, MemSeg, SoftPatch+, EfficientAD, MVTec AD 2: none stratify by size under compression |
| 49 | 2026-10-11 | S2 lookups | HR-Pro, distribution-aware refinement, 3D size survey, Memory Pollution | 4 | abstracts only |
| 50 | 2026-10-11 | doi.org | 10.1109/ACCESS.2026.3725847 → IEEE 11661333 | 1 | IEEE page not readable by fetcher |
| 51 | 2026-10-11 | WebSearch | HR-Pro Hierarchical Residual Prototype Memory ... IEEE Access | 0 | not indexed by web search |
| 52 | 2026-10-11 | WebSearch | prototype memory compact anomaly detection under-represented normal patterns small defects missed compression PatchCore 2026 | 2 | Lite PatchCore; ASO |
| 53 | 2026-10-11 | S2 Graph API | references + citations of arXiv:2607.04894 (ProCon backward/forward) | 0 new | refs: SPADE, PaDiM, PatchCore, SoftPatch, GraphCore, CFA, ensembles; 1 citation (2608.23299) |
| 54 | 2026-10-11 | arXiv PDF grep | 2603.20288, 2605.27748, 2604.06435, 2608.15277, Lite PatchCore PDF | 0 | none has defect-size analysis |
| 55 | 2026-10-11 | arXiv API | abs:"memory bank" AND abs:anomaly AND abs:budget / coreset+size / NN+small defects / memory bank+coverage / "defect size" / size-stratified / small anomalies eval / "greedy coreset" / FPS+memory / redundan | 2 | nothing new beyond SuperADD, LUMIN |
| 56 | 2026-10-11 | WebSearch | "coreset" subsampling hurts "small" anomalies localization per-region recall memory bank size study industrial | 0 | — |
| 57 | 2026-10-11 | WebSearch | openaccess.thecvf.com 2025 2026 workshop memory bank coreset anomaly detection efficiency analysis VAND | 1 | **SubtleDC (CVPRW 2026)** |
| 58 | 2026-10-11 | WebSearch | Pattern Recognition OR Neurocomputing 2025 2026 memory bank compression industrial anomaly detection coreset clustering prototype small defect | 0 new | — |
| 59 | 2026-10-11 | WebSearch | SubtleDC Drift-Guided Coreset Selection ... / "Sequential Coreset Sampling" anomaly | 1 | RareCLIP SCS (zero-shot; out of scope) |
| 60 | 2026-10-11 | CVF open access (curl) | CVPR2026_workshops/SVC listing + SubtleDC PDF + bib; CVPR2022 PatchCore bib | 2 | SubtleDC read; PatchCore pages 14318-14328 |
| 61 | 2026-10-11 | doi.org (curl) | 10 DOIs (Lehr, FS-MVTecAD2, ASO, Costanzino, SoftPatch+, PatchCore CVPR, Access ×3, MAKE, CoDIT) | 10 resolved | all 302 to publisher |
| 62 | 2026-10-11 | S2 Graph API | FS on MVTec AD 2 (Tu 2026) abstract | 1 | "greedy coreset reference strategy degrades pixel-level performance" |
| 63 | 2026-10-11 | arXiv API | abs:"memory bank" AND abs:anomaly (newest 40); abs:PatchCore (newest) | 0 new | newest items up to 2610.09677; no scoop |

Vocabulary harvested from early hits and then searched: "memory budget", "coreset ratio / sampling rate / subsampling ratio", "representative distance curve" (ASO), "global coverage / farthest-first / Local FF / Global FF" (Chae), "memory composition / contamination amplification", "prototype memory + residual normal patches" (HR-Pro), "density sampling / Density-Coreset" (CPD), "product-quantized memory bank" (PatchCore-Lite), "greedy-continued coreset" (ContCore), "tiny anomalies / robustness to defect size ρ / quartile AUPRO" (Costanzino), "relative region size" (AUPIMO), "quantization drift / micro-defect" (SubtleDC), "wrong-neighbor rate / oracle inversion" (Memory Pollution).

Coverage caveats:
- The S2 citations endpoint returned 1,941 PatchCore citations. That is likely fewer than the true count, and many records had no abstract, so I also filtered by title.
- Three S2 keyword-search calls failed on rate limits.
- Google Scholar was not queried directly. Semantic Scholar, the arXiv API and general WebSearch stood in for it.

---

#### 2. Anchor papers: detailed reading notes

### 2.1 PatchCore: Roth et al., "Towards Total Recall in Industrial Anomaly Detection", CVPR 2022 (arXiv 2106.08265v2; DOI 10.1109/CVPR52688.2022.01392)
Read from the arXiv v2 PDF (full text + supplement).

- **Coreset algorithm (Sec. 3.2, Alg. 1).** The minimax facility-location objective `M*_C = argmin_{M_C⊂M} max_{m∈M} min_{n∈M_C} ||m−n||_2` is solved with the iterative greedy approximation of Sener & Savarese. Distances are computed after a Johnson–Lindenstrauss random linear projection ψ: R^d→R^{d*}, d*<d, following Small-GAN. **The paper does not state d\*.** The official code (`src/patchcore/sampler.py`) uses `dimension_to_project_features_to=128`. `ApproximateGreedyCoresetSampler` uses `number_of_starting_points=10`.
- **Coreset ratios reported.** PatchCore-25%, -10% and -1% appear in Tables 1–3. Fig. 5 plots greedy coreset vs random subsampling vs learned basis proxies across target percentages, with PRO in Supp. Fig. S6. Quoted text: the paper says coreset "performs better than the other possible choices", and that no subsampling is "comparable to a coreset-reduced memory bank that is two orders of magnitudes smaller". Between roughly 50% and 10%, joint detection plus localisation "partly increase[s]". Memory usage at test time rises from under 30% (full bank) to nearly 95% (1% coreset). Reducing memory by striding instead hurts: s=2 gives 97.6 I-AUROC and s=3 gives 96.8.
- **Table 5 (mean over MVTec, as image AUROC, pixel AUROC, PRO):** 100% = (99.1, 98.0, 93.3), 0.6 s; 10% = (99.0, 98.1, 93.5), 0.22 s; 1% = (99.0, 98.0, 93.1), 0.17 s; 100%+IVFPQ = (98.0, 97.9, 93.0).
- **Tables 1–3 means:** I-AUROC 99.1 / 99.0 / 99.0 (25/10/1%); P-AUROC 98.1 / 98.1 / 98.0; PRO 93.4 / 93.5 / 93.1.
- **Table 4 (PatchCore-1%, bigger settings):**
  - WRN-101 (2+3) at 280: 99.4 / 98.2 / 94.4.
  - WRN-101 (1+2+3) at 280: 99.2 / 98.4 / 95.0.
  - Ensemble DenseN-201 & RNext-101 & WRN-101 at 320: **99.6** / 98.2 / 94.9.
  - The official README gives the WR50 baseline as 99.2 / 98.1 / 94.4 and the ensemble as 99.6 / 98.2 / 94.9.
- **Setup.**
  - WideResNet50, features from blocks 2 and 3 aggregated.
  - Neighbourhood patch size p=3, chosen by ablation (Fig. 4).
  - Images resized to 256×256 then centre-cropped to 224×224, with no augmentation.
  - Anomaly map is bilinearly upsampled and smoothed with a Gaussian σ=4 (not tuned).
  - faiss is used for NN search.
- **Reweighting (Eq. 7).** s = (1 − exp‖m^test,* − m*‖ / Σ_{m∈N_b(m*)} exp‖m^test,* − m‖)·s*, with N_b the b nearest memory features of m*. **The paper does not state b.** The official CLI uses `--anomaly_scorer_num_nn 1`.
- **Defect size.** There is no size-stratified analysis. Supp. C.3: localisation improves consistently with resolution (288/360/448). Supp. C.4 says false negatives include "finegrained anomalies that could be captured when moving to higher image resolutions" (gray category in Fig. S2). It is qualitative only and not tied to coreset ratio.
- **Limitations stated.** Only the transferability of pretrained features.
- **Implication for us.** The 1%-vs-100% claim rests on means of I-AUROC / P-AUROC / PRO. Per-category tables exist for 25/10/1%. No compression × defect-size analysis was performed.

### 2.2 ProCon: Chae et al., "ProCon: Projection-Consistency Memory for Training-Free Anomaly Detection", arXiv 2607.04894v1 (6 Jul 2026)
Read in full (main text + supplement).

- **Method.**
  - Frozen DINOv2 ViT-B/14 at 392×392 (28×28 patch grid), layers {−3, −6, −8, −9}.
  - Independent per-layer k-center coresets.
  - B=5 seed-perturbed banks per layer. The seed changes the coreset's random 192-d sub-projection and its starting points.
  - Soft projection onto k=5 nearest anchors; the projection residual is the anomaly evidence.
  - Bank-wise median, then layer-wise mean, then top-mean image readout (ratio 0.005).
- **Budgets.** 5% coreset for MVTec AD and VisA, 1% for Real-IAD. All ablations use 1%.
- **Memory-budget analysis.**
  - Table 4 (main) and Tables 16/17 (supplement) sweep 1/5/10% for SPM (the single-layer soft-projection baseline) vs ProCon.
  - MVTec P-AP: SPM 69.6 / 70.1 / 70.1; ProCon 73.0 / 73.5 / 73.6.
  - VisA P-AP: 50.3 / 50.3 / 50.3 for SPM and 52.3 for ProCon at every budget.
  - The authors conclude both methods "saturate at 5%". Their point is that the readout geometry, not the anchor count, drives the gain.
  - They also argue (Discussion) that a denser coreset can *worsen* false-normal matches.
- **Seed-perturbed bank analysis.**
  - Ladder (Table 2, MVTec, 1%): hard NN → +bank consensus (P-AP 67.4 → 68.5) → +soft projection (69.6) → +layer consensus (73.0).
  - The bank-count sweep (Table 10) finds monotone but small, saturating gains in B. One bank per layer already reaches P-AP 72.74, so B=1 is used for the cross-domain experiments.
- **Consensus analysis.**
  - Layer consensus beats every single depth (Table 3).
  - Concatenating layers before coreset selection is worse (Table 9). Their stated reason is that the coreset over-represents high-variance layers and under-represents fine-localisation layers.
- **Defect size.** No size-conditioned table. Size is mentioned only qualitatively:
  - Real-IAD P-AP is low because "many Real-IAD defects occupy very small regions".
  - Fine-texture, small-defect categories (toy bricks, mints) are hardest, with I-AUROC 82–86.
  - In MPDD, the P-AP spread is called "a defect-size artifact" (bracket_white P-AP 0.079 against AUPRO > 0.96).
- **Does it claim compression hurts small defects?** **No.** It claims the opposite direction: budget barely matters past 1–5% in aggregate. It names "compressed coresets" and ANN only as future-work speed-ups that "do not change the scoring objective".
- **Overlap with our claim.** ProCon only overlaps in method family (budget sweep on aggregate pixel metrics). It does not address the size-conditioned claim. Its saturation result is a *baseline observation our study must reproduce and then refine*.
- **Headline.** I-AUROC 99.8 (MVTec), 99.2 (VisA), 93.2 (Real-IAD). MVTec P-AP leads INP-Former by +3.3.
- **Evaluation details.** Single fixed evaluation seed. All 8 metrics reported. Hyperparameters were selected with a controlled protocol using a "bottom-3" validation subset of the *test* categories (Table 7). That is a mild test-set-selection concern.
- **Code.**
  - github.com/jw-chae/Procon. **No LICENSE file**: the GitHub API reports `license: null`, so the default is all rights reserved and the code cannot legally be reused or redistributed without permission.
  - Python 3.10, torch 2.5.1 + CUDA 12.1, torchvision 0.20.1, DINOv2 ViT-B/14 weights, MVTec-style folder layout. `--memory_ratio` is configurable.
  - There is no defect-size evaluation script.
- **Backward walk (S2 references).** SPADE, PaDiM, PatchCore, SoftPatch, GraphCore, CFA, DeSTSeg, UniAD, RD, DRAEM, DAAD block memory, CFLOW, VT-ADL, EfficientAD, INP-Former, plus ensemble literature (LSCP, feature bagging, etc.). None studies defect-size-conditioned compression. **Forward:** one citer, 2608.23299 (same group).

---

#### 3. Closest-paper matrix

| # | Paper (venue, year, verified URL) | Problem | Method family | Benchmark(s) | Headline number | Code? (URL, official/unofficial, licence) | Measures defect-size effect? | Studies memory budget / compression? | How our topic differs |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Roth et al., PatchCore (CVPR 2022) https://arxiv.org/abs/2106.08265 ; DOI 10.1109/CVPR52688.2022.01392 | Cold-start IAD | kNN patch memory + approx-greedy k-center coreset | MVTec AD, MTD, mSTC | I-AUROC 99.1 (25%), 99.6 ensemble; 1% ≈ 100% in mean (99.0/98.0/93.1) | github.com/amazon-research/patchcore-inspection, official, Apache-2.0 | No (qualitative only: fine-grained FNs need higher resolution) | **Yes**: 25/10/1% plus Fig. 5 subsampler curve, aggregate only | We condition the same budget sweep on defect area and test whether the aggregate parity hides small-defect loss |
| 2 | Chae et al., ProCon (arXiv 2026) https://arxiv.org/abs/2607.04894 | Training-free AD with robust memory readout | Soft projection + seed-perturbed coreset banks + layer consensus | MVTec AD, VisA, Real-IAD, MPDD, BTAD, Uni-Medical | I-AUROC 99.8/99.2/93.2; MVTec P-AP ≈73.5 | github.com/jw-chae/Procon, official, **no licence** | No (qualitative mentions only) | **Yes**: 1/5/10% sweep, aggregate P-AP; B sweep | We study size-conditioned compression effects; ProCon reports only budget saturation in aggregate |
| 3 | Kamiya, Yamashita, Hotta, ASO PatchCore (VISAPP 2026) DOI 10.5220/0014445100004084 (PDF https://www.scitepress.org/Papers/2026/144451/144451.pdf) | Pick the coreset size automatically | Knee point on the normalised greedy representative-distance curve | MVTec AD, VisA, MVTec AD 2 | 86.5% / 88.6% / 85.1% memory reduction vs 10% PatchCore, "comparable" I/P-AUROC/PRO (e.g. VisA PRO 97.9→97.6) | None found | No | **Yes**: the central claim is that aggregate accuracy holds under ~7× compression; Fig. 1 says I-AUROC saturates above ~2% | **Prime target**: exactly the "aggregate unchanged" claim our hypothesis challenges; it never checks small defects |
| 4 | Chae, Wang, Qin, "What Memory Composition Does Not Tell Us About Anomaly Detection" (arXiv 2026) https://arxiv.org/abs/2608.23295 | How coverage selection admits contamination | Selector comparison (random, medoid, Local FF, Global FF) + CleanCon OOB gate | MVTec AD (+VisA etc.), PatchCore and DINOv2/ProCon paths | Global FF amplifies contamination 16–41× at a 1% budget; CleanCon raises macro P-AP in 12/12 comparisons | github.com/jw-chae/cleancon (licence not checked) | No | **Yes**: budgets 0.1–10%, matched absolute K, selectors compared; appendix "risk-aware coverage control" | Same "coverage under budget" lens, but the outcome is contamination, not defect size. Closest methodological template (matched-K controls) |
| 5 | Chae, Wang, Qin, "What Remains Normal? Clean Images Miss Useful Near-Defect Normal Patches" (arXiv 2026) https://arxiv.org/abs/2608.23299 | Normal-coverage gaps near defects | Fixed-budget oracle candidate pools + BoundarySupport synthetic context | MVTec AD, VisA, Real-IAD | Fixed-budget GT-normal oracle P-AP 73.34→76.95; near-defect (≤2 cells) recovers 94.70% | github.com/jw-chae/boundary_support (licence not checked) | Partially: distance-to-defect stratification, not defect size | Fixed budget held constant; candidate identity varied | Shows coverage of *normal* neighbourhoods near defects matters at fixed budget. Our study varies the budget and conditions on defect size |
| 6 | Feng et al., HR-Pro (IEEE Access 14:134267–134284, 2026) DOI 10.1109/ACCESS.2026.3725847 (abstract only) | Compact memory without accuracy loss | Hierarchical prototype memory + **residual normal patches for under-represented patterns** + score fusion | MVTec AD, VisA | Storage −73.4% (MVTec) and −76.1% (VisA) vs PatchCore-10%; >150× faster | Not stated in abstract | Not in abstract | **Yes** | **Pre-empts the "coverage-preserving correction" idea** (residual coverage under compression); no size conditioning reported in abstract |
| 7 | Stropeni et al., PatchCore-Lite / PaDiM-Lite (CoDIT 2026; arXiv 2603.20288) https://arxiv.org/abs/2603.20288 ; DOI 10.1109/CoDIT70676.2026.11630815 | Edge deployment | Product-quantised memory, coarse-to-fine search | MVTec AD, VisA | −79% total memory for PatchCore-Lite | Not checked | No (grep: no size analysis) | **Yes** (PQ compression) | Compression axis differs (PQ, not subsampling); aggregate only |
| 8 | Lardon, Guis, Busvelle, Lite PatchCore (VISAPP 2026) DOI 10.5220/0014253200004084 | Embedded robot inspection | Early-stopped coreset + multi-class unification + PCA | MVTec AD, VisA | >98% memory-bank reduction, +3% instance AUROC | Not found | No | **Yes** (early-stopping coreset size) | Again aggregate-only "compression is free" evidence |
| 9 | Costanzino et al., "Learning to Be a Transformer to Pinpoint Anomalies" (IEEE Access 13:109624–109637, 2025; arXiv 2407.04092) https://arxiv.org/abs/2407.04092 ; DOI 10.1109/ACCESS.2025.3582900 | Tiny defects lost to downsampling | Teacher–student MLPs on ViT attention mappings; **size-robustness metrics** | MVTec AD, VisA (full-res GT, no centre crop) | VisA Q1-AUPRO@30%: 0.935 vs PatchCore 0.739; ρ@5% 0.702 vs PatchCore 0.454 | Official code per paper (not checked) | **Yes**: cumulative-quartile AUPRO@30%/@5% per object; ρ = mean-AUPRO·(1−\|Q4−Q1\|/max) | No (PatchCore at default coreset only) | Supplies a ready size-conditioned protocol. Warns that **MVTec AD "provides stable performance across sizes"**, which risks a null result on MVTec-only |
| 10 | Bertoldo et al., AUPIMO (BMVC 2024; arXiv 2401.01984) https://arxiv.org/abs/2401.01984 | Metric saturation | Per-image overlap metric, low FPR tolerance | MVTec AD, VisA (incl. PatchCore) | Shows MVTec/VisA not "solved" | github.com/jpcbertoldo/aupimo; in anomalib | Partially: reports region-size distributions (MVTec mostly 1e-3..1e-1 relative size; VisA down to ~1e-6) | No | Gives the size-distribution facts we need; no compression |
| 11 | Shinde, SubtleDC (CVPR 2026 Workshops, pp. 1376–1384) https://openaccess.thecvf.com/content/CVPR2026W/SVC/html/Shinde_SubtleDC_Drift-Guided_Coreset_Selection_for_Robust_Few-Shot_Industrial_Anomaly_Detection_CVPRW_2026_paper.html | Encoder PTQ + few-shot memory | Drift-score-guided normal-image selection | MVTec AD, VisA (ResNet-18, EffNet-B0; FP32/INT8/NF4) | I-AUROC near FP32 at low support sizes | Not stated | No. It *asserts* that quantization damages "micro-defect detection" but evaluates I-AUROC only | Compression of the *encoder* (PTQ), plus a support-set budget | Closest to the "compression hurts subtle defects" narrative, but never measures size; compresses a different component |
| 12 | Tu, "Few-Shot AD on MVTec AD 2: A Systematic Study and a Strong Frozen Baseline" (IEEE Access 14:152500–152511, 2026) DOI 10.1109/ACCESS.2026.3733273 (abstract only) | Few-shot benchmark on small-defect-heavy MVTec AD 2 | DINOv2 memory NN baseline vs PatchCore/WinCLIP/AnomalyDINO | MVTec AD 2 (+AD v1, LOCO) | pAUPRO@0.30 0.621 vs PatchCore 0.426 (8-shot) | "will be released" | Unknown from abstract | **Partially**: finds "greedy coreset reference strategy degrades pixel-level performance at both evaluated reference budgets" | Evidence that coreset hurts pixel-level results where defects are small; few-shot, not size-stratified (per abstract). Must read full text before the main study |
| 13 | Lehr et al., "Limitations of anomaly detection: beyond which size defects can be reliably recognized" (ICMV 2023, Proc. SPIE 13072, 130720H, 2024) DOI 10.1117/12.3023615 (abstract only) | Minimum detectable defect size | Synthetic growing defect (11 steps) | 2 in-house problems | Reliable detection from 0.03% relative pixel area | Not stated | **Yes** (size sweep) | No | Size-sensitivity curve without memory compression |
| 14 | Deng et al., CPD-PatchCore (IEEE Access 14:138352–138362, 2026) DOI 10.1109/ACCESS.2026.3731018 (abstract only) | Sub-mm defects on piston rods + memory efficiency | Cross-scale edge-preserving pyramid + **Density-Coreset** sampling | Custom piston-rod dataset | −90% memory bank, +30.38% speed vs PatchCore | Not stated | Motivated by sub-mm defects; no size-stratified result in abstract | **Yes** | An alternative coverage/density coreset aimed at small defects, but on a private dataset and not a controlled size study |
| 15 | Villanueva López et al., "Memory Pollution in Multi-Product VAD" (MAKE 8(7):219, 2026) DOI 10.3390/make8070219 (abstract only) | Shared-bank interference | Wrong-neighbour rate, analytic model vs memory budget, router | Multiple datasets | Up to 25× memory reduction | Not stated | No | **Yes**: an analytic WNR-vs-budget model; "oracle inversion" at fixed budget | Budget-dependent failure analysis, but across products, not defect size |

Other memory/coreset papers I resolved and screened out (no defect-size analysis, or a different problem):
- **Continual / streaming coresets:** ContCore (BMVC 2026, 2608.15277), CADIC (2511.08634), DINOSaur (ECCV 2026, 2605.24251), on-device CL PatchCore (2512.13497), continual edge benchmark (2604.06435), Mahalanobis PatchCore (2605.27748, streaming bounded-memory build), Sequential PatchCore (2501.09579, sequential coreset; reports defect-wise recall but not per budget).
- **Noisy or long-tail memory selection:** SoftPatch (NeurIPS 2022, 2403.14233), SoftPatch+ (Pattern Recognition 2025, DOI 10.1016/j.patcog.2024.111295), TailedCore (CVPR 2025, 2504.02775).
- **Fast samplers and efficiency:** LUMIN PSP sampler (2609.04775), FAPM adaptive coreset (ICASSP 2023, 2211.07381), PatchCore-Q (ICAIIC 2026, DOI 10.1109/ICAIIC68212.2026.11454205), MAD-Flow FPGA INT4 kNN (IEEE IoT-J 2025, DOI 10.1109/JIOT.2025.3605880), tiled ensemble (CVPRW 2024, 2403.04932).
- **Memory editing:** HITL memory correction (2608.17775).
- **Few-shot memory or feature-adapted memory:** AnomalyDINO (WACV 2025, 2405.14529), GraphCore (2301.12082), CFA (2206.04325), PNI (2211.12634), MemSeg (2205.00908).
- **Challenge pipelines:** SuperAD and SuperADD (2505.19750, 2605.14808; SuperADD changes subsampling for "better coverage").
- **Other:** Learnable PQ for AD (Neurocomputing 2024, DOI 10.1016/j.neucom.2024.127532; abstract unavailable).

---

#### 4. Reading notes (closest papers)

**ASO PatchCore (VISAPP 2026).**
- *Measured:* MVTec AD (15 categories), VisA (12), MVTec AD 2 (8). Metrics are I-AUROC, P-AUROC, PRO, memory ratio relative to 10% PatchCore, and ms per image. Ten trials per category, averaged.
- *Tuned vs default:* the knee point is chosen automatically per category from the normalised curve of representative distance d(k) against k. Everything else is PatchCore default.
- *Results:*
  - MVTec AD: memory 13.5% of the 10% baseline; I-AUROC 99.1 vs baseline (≈ equal); PRO 97.4 vs 97.3 (their PRO variant gives values in the high 90s, so check the integration limit).
  - VisA: memory ratio 11.4%; I-AUROC 94.7→94.5, P-AUROC 98.6→98.3, PRO 97.9→97.6.
  - Worst per-category I-AUROC drop: 0.7 pt (screw, MVTec).
- *Ablation:* none on defect size.
- *Limitation as written:* none on small defects. Fig. 1 claims I-AUROC saturates above ~2%.
- *Use for us:* a ready baseline whose "comparable accuracy" claim can be stress-tested by defect size (VisA and MVTec AD 2 contain many small defects).

**What Memory Composition Does Not Tell Us (2608.23295).**
- Under a fixed representation and fixed absolute K (1% of the unfiltered pool), it compares four selectors (patch-random, image-balanced random, medoid, Local FF, Global FF) and budgets of 0.1–10%.
- Global coverage (farthest-first) preferentially retains rare patches, which here means contamination.
- The outcome metric is category-macro P-AP. There is no defect-size conditioning.
- An appendix runs a "risk-aware coverage control" that replaces high-risk centres.
- *Relevance:* it shows the k-center objective's rarity bias. Under compression that same bias should also keep rare *normal* modes. This is the mechanism our "coverage" hypothesis relies on, and it predicts the *opposite* of random subsampling. Our study should include random and medoid selectors as controls, as this paper does.

**What Remains Normal? (2608.23299).**
- At a fixed bank budget, adding GT-normal patches from defect images raises MVTec P-AP from 73.34 to 76.95. Of that gain, 94.70% comes from patches within two cells of the defect.
- Score reductions are spatially selective: largest on normal patches next to defects, in all 15 categories.
- *Relevance:* coverage gaps near defect boundaries limit localisation. For small defects, boundary pixels are a larger share of the region, so a size effect is plausible. It is not measured.

**Costanzino et al. (2407.04092 / IEEE Access 2025).**
- *Protocol:*
  - Evaluation on full-resolution ground truth with no centre crop (they disable PatchCore's crop) and padding removed.
  - Per object category, the anomaly-size distribution is split into cumulative quartiles: Q1 holds only the smallest defects, Q4 holds all.
  - AUPRO@30% and AUPRO@5% are computed on each set.
  - ρ = w·(1−s), where w is the mean AUPRO over Q1..Q4 and s = |AUPRO(Q4)−AUPRO(Q1)| / max(·).
- *Findings:*
  - On VisA, Q1 is below Q4 for every method.
  - PatchCore Q1-AUPRO@5% is 0.484 and ρ@5% is 0.454.
  - On MVTec AD, Q1 and ρ are "quite consistently higher for all methods", and MVTec "provides stable performance across sizes".
- *Not studied:* coreset ratio. PatchCore is run at default.
- *Implication:* a size-conditioned metric already exists, so we should not claim a new metric. The MVTec-only scope may give a weak signal, so VisA / MVTec AD 2 should be added as a robustness check.

**Tu 2026 (MVTec AD 2 few-shot).** Abstract only. "The tested greedy coreset reference strategy degrades pixel-level performance at both evaluated reference budgets" (1–8 shots) on a dataset known for extremely small defects. Full text is needed: if it reports per-size results, it is closer than it looks.

**SubtleDC (CVPRW 2026).** The motivation states that quantization drift "is especially damaging" to micro-defect detection. Experiments report only image AUROC against support size and quantization level. The core-set ratio r=0.25 is fixed. It does not measure the size effect.

**HR-Pro (IEEE Access 2026).** Abstract only, since IEEE Xplore was not readable. The design adds "a small set of residual normal patches that are insufficiently represented by prototypes, thereby improving the coverage of under-represented normal patterns while maintaining compact memory storage". It reports strong pixel-level localisation relative to PatchCore-10%. Whether it stratifies by defect size is unknown, so the full text must be checked.

---

#### 5. Citation walks

- **PatchCore forward (S2, 1,941 citing records).** Keyword filters on title and abstract (coreset / subsampl / memory bank / compress / budget / small / tiny / size / efficient / quantiz / lite) gave about 40 candidates (listed in §3 and the screen-out list).
  - None reports detection or localisation stratified by defect area as a function of memory budget.
  - The closest are ASO PatchCore, HR-Pro, Lite PatchCore, PatchCore-Lite, CPD-PatchCore, PatchCore-Q, Memory Pollution, Tu 2026, and the Lehr size-limit paper.
- **ProCon backward.** Listed in §2.2; nothing on size or compression. ProCon forward: one citer, 2608.23299.
- **Chae group (author search).** ProCon, What-Memory-Composition, What-Remains-Normal, StructCore, GCR. This group is actively publishing controlled memory-composition studies (Jul–Sep 2026), and the coverage question is squarely in its programme. **This is the most likely group to scoop a size-conditioned compression study next.**

---

#### 6. Preliminary novelty assessment

**Verdict.** The diagnostic claim is **Clear, but in a thin gap**: no paper found measures how memory-bank compression changes small-defect sensitivity, stratified by defect area, at matched budgets. The proposed correction is **Crowded**.

Reasoning (adversarial):
- **Budget sweeps on aggregate metrics are common.** PatchCore, ProCon, ASO PatchCore, Lite PatchCore, PatchCore-Lite, HR-Pro, CPD-PatchCore and What-Memory-Composition all report them, and all conclude, or assume, that compression is nearly free. **Not one conditions on defect size.** PatchCore and ProCon mention small or fine-grained defects only qualitatively.
- **Size-conditioned metrics already exist** (Costanzino quartile-AUPRO and ρ; AUPIMO size analysis; the Lehr size sweep). None crosses them with memory budget. This lowers the novelty of any "new metric" and raises the feasibility of the study.
- **Partial-scoop signals:**
  - Tu 2026 finds greedy coreset degrades pixel-level performance on MVTec AD 2 (few-shot). If its full text shows a size breakdown, the gap narrows.
  - SubtleDC asserts that compression of the encoder hurts micro-defects, but never measures it.
- **The correction direction is crowded:**
  - HR-Pro (residual coverage patches under compression).
  - CPD-PatchCore (density coreset for sub-mm defects).
  - CleanCon / risk-aware coverage (2608.23295).
  - SuperADD's coverage-oriented subsampling.
  - ContCore (greedy-continued coreset).
  - ASO (knee-point budget).
  - A new "coverage-preserving coreset" would need to beat these, especially HR-Pro.
- **Empirical risk.** Costanzino reports MVTec AD as size-stable. PatchCore and ProCon show 1%≈10%≈100% in aggregate. On MVTec only, the effect may be small or null. Plan VisA / MVTec AD 2 as secondary sets, and pre-register a null-result framing (a "compression is size-neutral down to X%" finding is still publishable as a negative or diagnostic result).

**Closest 3 and the delta:**
1. **ASO PatchCore (VISAPP 2026).** It claims about 86% coreset-memory reduction with "comparable" I-AUROC, P-AUROC and PRO. We test whether that parity breaks for the smallest defect-area quantiles at the same budgets.
2. **ProCon (arXiv 2607.04894).** Its 1/5/10% sweep reports aggregate P-AP saturation and seed-perturbed bank stability. We condition the same budget and seed sweep on per-region defect area and show what the aggregate hides.
3. **Costanzino et al. (IEEE Access 2025).** It defines size-quartile AUPRO and the ρ robustness metric, but evaluates PatchCore at one default memory. We sweep memory budget and selector under that protocol and attribute size-robustness changes to coverage.

(Runner-up threats: HR-Pro for the correction; Tu 2026 for coreset harming pixel-level results on small-defect data; What-Memory-Composition for the matched-K, selector-controlled methodology.)

**Must-do before committing:**
- Get the full text of Tu 2026 and HR-Pro. Both are IEEE Access, and Tu is gold OA (CC-BY); try a browser download, since the fetcher got nothing.
- Re-run this search in about 4 weeks targeting the Chae group (au:Joongwon_Chae) and "coreset AND size".

---


---

## Appendix B — search pass B (evaluation protocol & baselines), 2026-10-11, full record

> Correction (verified by me): B's statement that no paper reports MVTec AD by defect size is wrong — see §1 (Costanzino et al. 2025).

### Phase-0 Literature Verification — B: Evaluation Protocol & Baselines (MVTec AD)

Verification date: **2026-10-11**. Every item below was resolved live today (WebSearch, WebFetch, `curl` of arXiv/CVF/GitHub raw files, `export.arxiv.org` API, `api.semanticscholar.org`, GitHub REST API via `gh`). Nothing is cited from memory. Items that could not be resolved from a primary source are marked **[UNRESOLVED]** or **[SECONDARY]** (verified only through a secondary source or search snippet). Statements that are my reading of code (not stated in text by authors) are marked **[INFERRED FROM CODE]**.

Downloads policy followed: no dataset, no tarball/archive was downloaded. Only paper PDFs (arXiv/CVF/DNB open copies) and individual source/README files were fetched for reading. The EfficientAD `per_scenario_results.json` (200 KB, MVTec mydrive) was only HEAD-checked, not downloaded (needs your OK if wanted).

---

#### 0. TL;DR — Frozen protocol recommendations

1. **Data**: original MVTec AD, 15 categories, official split, no validation images taken from test. Totals verified (IJCV Table 1): 3629 train-good / 467 test-good / 1258 test-defective / 1888 GT regions / 73 defect types; 5354 images. Grid, screw, zipper are single-channel (convert to 3-ch for ImageNet backbones).
2. **Primary localisation metric: AU-PRO@0.3** computed with the **official MVTec algorithm** (exact, all unique thresholds; 8-connected GT components via `scipy.ndimage.label(gt, np.ones((3,3)))`; FPR over **all** defect-free pixels of **all** test images incl. good images; PRO averaged over all GT regions in the category; trapezoid integration to FPR=0.3 with linear interpolation at the limit; divide by 0.3). Vendor `pro_curve_util.py` + `generic_util.trapezoid` (BSD-3-style licence, "Copyright 2022 MVTec Software GmbH", redistribution allowed with notice) — *do not* use RD4AD/old-anomalib PRO variants.
3. **Report also** AU-PRO@0.05 (MVTec AD 2 convention for tight FPR), pixel AUROC (for comparability only; flagged as large-defect-dominated), image AUROC (score = max of anomaly map, as official script uses `np.max`) and optionally AUPIMO (per-image, normal-image FPR axis).
4. **Resolution protocol**: evaluate anomaly maps **at original GT resolution, full field of view, no center crop**. The PatchCore default (resize 256, center-crop 224 = central 76.6 % of area) changes the evaluated pixels and GT; EfficientAD authors explicitly disabled it for fairness. If the 224 crop is used for feature extraction, map back to full image (pad/upsample) before scoring, or run the uncropped variant (resize to 224/256 square without crop) as the headline and the cropped variant as a "paper-reproduction" sanity check.
5. **Size stratification (the project's core)**: define size bins on GT **connected components (8-connectivity, at native resolution)** — not images — and report per-bin region recall at fixed normal-pixel FPR operating points (e.g. FPR = 0.01/0.05/0.3) plus per-bin AU-PRO. This is a direct decomposition of the official PRO (which already averages over regions), so it remains reviewer-legible. Pixel AUROC must not be used to argue small-defect effects (MVTec AD 2 paper, Fig. 4: TPR "dominated by large anomalies").
6. **No test-set tuning**: hyper-parameters fixed a priori (coreset ratio grid is the independent variable, not tuned). MVTec AD 2 paper explicitly criticises test-set tuning; EfficientAD disables early stopping/crop tuning for the same reason.
7. **Seeds/statistics**: ≥3 seeds for stochastic parts (random projection in approximate greedy coreset, PatchCore `ApproximateGreedyCoresetSampler`), report mean±std per category and category-macro mean; paired tests over the 15 categories (AUPIMO paper argues for per-image statistical tests).

**EfficientAD verdict**: **No official code exists** (verified: arXiv page, CVF page, MVTec publications page list only the PDF; every GitHub implementation found self-labels "unofficial"). Exact reproduction **requires ImageNet** twice: (a) distilling WRN-101 PatchCore features into the PDN teacher on ImageNet (App. A.2), and (b) the "pretraining penalty" that samples an ImageNet image at **every** student training step (Sec. 3.2). The unofficial nelson1425 repo ships third-party teacher weights and requires ImageNet for the penalty; anomalib substitutes **Imagenette** and downloads its own teacher weights → not an exact reproduction (anomalib's own MVTec image AUROC: S 0.982 / M 0.975 vs paper 98.8 / 99.1). **A compliant, exact, ImageNet-free reproduction is NOT feasible.** If included at all, label it "EfficientAD (unofficial nelson1425, penalty disabled / Imagenette)" as a secondary comparator; paper ablation says removing the penalty costs −0.4 pp mean AU-ROC (avg of 3 dataset collections).

**Recommended feasible baselines (Colab, training-free/normal-only)**: (1) PatchCore official (amazon-science, Apache-2.0, WRN-50 torchvision weights, faiss-cpu/gpu) — the anchor; (2) PatchCore coreset ratios {100 %, 25 %, 10 %, 1 %, …} + **random subsampling** control (PatchCore paper §3.2/Fig. 3 already contrasts coreset vs random); (3) PaDiM (via anomalib, Apache-2.0; no official code) — Gaussian density baseline; (4) SPADE (kNN image+pixel; unofficial byungjae89 Apache-2.0 or a 30-line re-implementation inside the PatchCore code path with no coreset, k-NN) — the "no compression" memory baseline; (5) optional AnomalyDINO (WACV 2025, Apache-2.0, DINOv2 patch memory, training-free) as a modern backbone check. CFA, PNI, CPR, SoftPatch, GraphCore are either trained, unlicensed, or not runnable on budget — cite, do not run (details §B).

---

#### A. EVALUATION PROTOCOL

### A1. MVTec AD papers, PRO/AU-PRO definition, counts, known issues

**Sources (fetched today)**
- CVPR 2019 paper PDF: https://openaccess.thecvf.com/content_CVPR_2019/papers/Bergmann_MVTec_AD_--_A_Comprehensive_Real-World_Dataset_for_Unsupervised_Anomaly_CVPR_2019_paper.pdf (pp. 9584–9592, DOI 10.1109/CVPR.2019.00982 via Semantic Scholar).
- IJCV 2021 paper: DOI 10.1007/s11263-020-01400-4, IJCV 129:1038–1059, open access CC BY (S2 API). Springer pages returned 303→login for curl/WebFetch today; full text read from the open copy at the German National Library https://d-nb.info/1226611842/34 (header shows the IJCV DOI; "Received 15 April 2020 / Accepted 2 November 2020; © The Author(s) 2021").
- Uninformed Students (CVPR 2020), arXiv 1911.02357 — where the 30 % FPR AU-PRO convention is first operationalised.

**PRO definition (IJCV Sec. 4.2, Eq. 9; verified text)**: for each test image the GT is decomposed into connected components; PRO = (1/N) Σ_i Σ_k |P_i ∩ C_{i,k}| / |C_{i,k}|, N = total number of GT components in the evaluated dataset (category). "The PRO metric averages the TPR over each ground truth region instead of averaging over all image pixels." The paper motivates it as "especially useful if the detection of smaller anomalies is considered equally important as the detection of larger ones."

**Integration limit / normalisation (verified)**:
- IJCV Sec. 4.3: only 2.7 % of all test pixels are anomalous; "For FPRs as low as 30 % the segmentation result is already degenerated"; areas are computed "only up to a certain false positive rate. To ensure that the maximum attainable values ... is equal to 1, we normalize the resulting area." Sec. 6.2: "computation of curve areas that involve the false positive rate is performed up to an FPR of 0.3 if not mentioned otherwise." Appendix tables: "Normalized area under the PRO curve up to an average false positive rate per-pixel of 30 %." IJCV also reports sensitivity with limits 0.01, 0.05, 1.0 and notes rankings change with the limit ("one must select it carefully").
- Uninformed Students (arXiv 1911.02357, Sec. 4): "We evaluate the PRO value for a large number of increasing thresholds until an average per-pixel false-positive rate of 30% for the entire dataset is reached ... We normalize the integrated area to a maximum achievable value of 1."
- **Connectivity**: the IJCV text does **not** state 4- vs 8-connectivity. The **official code** does: `structure = np.ones((3, 3), dtype=int)` → **8-connectivity** (see A2).
- **Threshold sampling**: official code uses **every unique anomaly score** as a threshold (exact curve via global sort + cumulative sums; ties merged), not a binned grid.
- **Handling of images**: FPR = cumulative false positives / number of all GT-negative pixels pooled over **all** test images of the category, including the defect-free test images (official `evaluate_experiment.py` appends an all-zero GT for good images). PRO pooled over all regions of all defective images of the category. Category means are then averaged across the 15 categories (EfficientAD Sec. 4: "we evaluate the respective metric for each scenario and then compute the mean across scenarios", following the dataset authors' policy).

**Per-category counts (IJCV Table 1 = CVPR19 Table 1, verified identical)**:

| Category | Train good | Test good | Test defective | Defect types | GT regions | Side (px) | Grayscale |
|---|---|---|---|---|---|---|---|
| carpet | 280 | 28 | 89 | 5 | 97 | 1024 | |
| grid | 264 | 21 | 57 | 5 | 170 | 1024 | yes |
| leather | 245 | 32 | 92 | 5 | 99 | 1024 | |
| tile | 230 | 33 | 84 | 5 | 86 | 840 | |
| wood | 247 | 19 | 60 | 5 | 168 | 1024 | |
| bottle | 209 | 20 | 63 | 3 | 68 | 900 | |
| cable | 224 | 58 | 92 | 8 | 151 | 1024 | |
| capsule | 219 | 23 | 109 | 5 | 114 | 1000 | |
| hazelnut | 391 | 40 | 70 | 4 | 136 | 1024 | |
| metal_nut | 220 | 22 | 93 | 4 | 132 | 700 | |
| pill | 267 | 26 | 141 | 7 | 245 | 800 | |
| screw | 320 | 41 | 119 | 5 | 135 | 1024 | yes |
| toothbrush | 60 | 12 | 30 | 1 | 66 | 1024 | |
| transistor | 213 | 60 | 40 | 4 | 44 | 1024 | |
| zipper | 240 | 32 | 119 | 7 | 177 | 1024 | yes |
| **Total** | **3629** | **467** | **1258** | **73** | **1888** | – | |

Note: "# Defect types" counts defect groups excluding "good"; table header in paper is "# Defect groups".

**Known dataset issues / quirks (verified)**
- **Annotation policy** (IJCV Sec. 3): "pixels on the border of anomalies or lying in ambiguous regions were preferably labelled as anomalous"; "For locally deformed objects, annotations were created on the deformed area as well as in the region where the deformed object part is expected to be located"; "Some defects manifest themselves as missing parts. In these cases, we annotated the expected location of the part as anomalous." → applies to e.g. transistor `misplaced` (missing/shifted transistor annotated at the expected location) and cable `missing_*`; these are logical/global anomalies where GT covers background-like pixels. [The category→defect-folder mapping (e.g. `transistor/misplaced`, `metal_nut/flip`) is from search snippets of secondary papers — **[SECONDARY]**; the folder names themselves are not in the paper text.]
- **Label ambiguity**: Zheng et al. 2022 "Benchmarking Unsupervised Anomaly Detection and Localization" (arXiv 2205.14852, Sec. 3.1.3 / Fig. 4) show unlabeled anomalous areas (screw "scratch neck", zipper "fabric interior") and inconsistent hazelnut "print" annotation (one fine, one coarse), and claim that "after correcting these annotations, the performance of the state-of-the-art method is basically close to a full score". No corrected masks were released that I could find. **No official MVTec errata exist on the dataset page** (page checked today: only dataset form, evaluation code link, CC BY-NC-SA 4.0 licence text).
- **Toothbrush**: only 60 train / 12 test-good / 30 test-defect, single defect type → very high variance per category (1 image = 2.4 pp image AUROC).
- **Transistor**: 60 good vs 40 defective test images; logical defects (`misplaced`). PatchCore official results.csv shows transistor as the weakest localisation category (anomaly_pro 0.83 for WR50).
- **Grayscale categories**: grid, screw, zipper are single-channel (IJCV Table 1 "Grayscale" column).
- **Center region**: EfficientAD paper (Sec. 4) measured "In the case of MVTec AD, 99.9 % of the defects lie fully or partially within this cropped area" (central 76.6 % from 256→224 crop) — i.e., center-crop protocols exploit a dataset bias. MVTec AD 2 explicitly adds "defects at the image border" for this reason.
- **Saturation**: MVTec AD 2 (arXiv 2503.21622 / IJCV 2026 DOI 10.1007/s11263-026-02743-0): MVTec AD "nearly saturates with the best model achieving 97.8% mean AU-PRO" (CPR, TIP 2024); SOTA models differ by <1 pp; "occasionally slightly adapted or approximated versions [of AU-PRO] are used"; "the common practice of tuning hyperparameters based on test data imply the inappropriate use of the test set".
- **Dataset licence**: CC BY-NC-SA 4.0 (MVTec page, verified).

### A2. Official MVTec evaluation code (`mvtec_ad_evaluation.tar.xz`)

- Link on the official page today: `https://www.mydrive.ch/shares/150450/.../439517473-1665675012/mvtec_ad_evaluation.tar.xz` (not downloaded). Page text: "we provide python scripts that allow an easy evaluation ... For details on the metrics used for the evaluation, we refer to our corresponding paper." No version/changelog/licence is printed on the page.
- Contents verified from **GitHub mirrors** that vendor the tarball (found via `gh search code`): e.g. `Sam-khanjani/AnomalyDetection/mvtec_ad_evaluation/` (README states it is based on nelson1425/EfficientAD, whose README downloads the official tarball), plus `TArdelean/AnomalyLocalizationFCA/evaluation/evaluate_experiment.py`, `tootouch/MemSeg/metrics/pro_curve_util.py`, `husmen/anometa/.../_pro_reference.py` ("Vendored from mvtec_ad_evaluation ... Copyright 2022 MVTec Software GmbH").
  - Files: `evaluate_experiment.py`, `evaluate_multiple_experiments.py`, `generic_util.py`, `pro_curve_util.py`, `roc_curve_util.py`, `print_metrics.py`, `threshold_computation.py`, `LICENSE.txt`, `README.md`, conda/requirements.
  - **What it computes** (README + code): area under the PRO curve (`--pro_integration_limit`, **default 0.3**, assert 0 < limit ≤ 1) and **image-level classification AU-ROC** with `scoring_function=np.max` over the anomaly map. Per-object JSON plus `mean_au_pro`, `mean_classification_au_roc`. **Does not compute pixel AUROC.**
  - Input contract: one `.tif/.tiff` anomaly map per test image at `<dir>/<object>/test/<defect>/<id>.tiff`; "their size must match the one of the original dataset images" → **full-resolution evaluation is mandated**.
  - `pro_curve_util.compute_pro`: `label(gt_map, np.ones((3,3)))` (**8-connectivity**); ok-pixels = label 0; fp increment per ok pixel; PRO increment 1/|region| per region pixel; global descending sort over all pixels of all maps; cumsum; FPR /= #ok pixels, PRO /= #regions; ties merged (keep last point per unique score); clip to ≤1; prepend (0,0), append (1,1).
  - `generic_util.trapezoid(x, y, x_max)`: trapezoid rule cut at x_max with **linear interpolation of y at x_max** (correction term); `au_pro /= integration_limit`.
  - **Licence** (`LICENSE.txt` in mirror): "Copyright 2022 MVTec Software GmbH" + BSD-3-Clause-style redistribution conditions (retain notice; no endorsement). `evaluate_experiment.py` header: `__author__ = "Paul Bergmann, David Sattlegger"`, `__copyright__ = "2021, MVTec Software GmbH"`. README: "The version of this evaluation script is: 1.0".
  - **[UNRESOLVED]** anomalib issue #3718 (2026-08-12) refers to "MVTec's official evaluation script v2.0"; the mirror I could read says 1.0. The tarball on the official page may have been updated (link timestamp 1665675012 ≈ Oct 2022, same as nelson1425's link 1665667812). Resolve by downloading the tarball yourself (not done per instructions) and diffing `pro_curve_util.py`.

### A3. PatchCore official code — how metrics are computed

Repo: https://github.com/amazon-science/patchcore-inspection — **Apache-2.0** (README + GitHub API). Last commit 2023-03-06 (`fcaa92f`); EfficientAD paper pinned commit `6a9a281` (2022-06-17).
- **Preprocessing** (`datasets/mvtec.py`): image `Resize(256) → CenterCrop(224) → ToTensor → Normalize(ImageNet mean/std)`; **mask gets the same Resize(256)+CenterCrop(224)** → all pixel metrics are computed on the 224×224 **center crop**, not at native resolution. [INFERRED FROM CODE] mask resize uses torchvision default (bilinear) and `metrics.py` binarises with `.astype(int)` (floor) → interpolated GT boundary pixels (<1.0) count as normal (slight GT erosion).
- **Backbone**: `backbones.py` → `models.wide_resnet50_2(pretrained=True)` (torchvision ImageNet weights; only weights, no ImageNet images). Layers `layer2`,`layer3`; `--pretrain_embed_dimension 1024 --target_embed_dimension 1024 --patchsize 3 --anomaly_scorer_num_nn 1`; `sampler -p 0.1 approx_greedy_coreset`.
- **Anomaly map** (`common.RescaleSegmentor`): bilinear `F.interpolate` (align_corners=False) of patch scores to 224, then `ndimage.gaussian_filter(sigma=4)` (paper §3: "smoothed the result with a Gaussian of kernel width σ = 4, but did not optimize this parameter"). Image score = max over patch scores (`patch_maker.score`).
- **Metrics** (`metrics.py`, `bin/run_patchcore.py`): image AUROC = sklearn `roc_auc_score`; pixel AUROC on flattened maps of **all** test images (`full_pixel_auroc`) and of **anomalous images only** (`anomaly_pixel_auroc`, `sel_idxs` = images with non-empty mask). Scores are min-max normalised per run (AUROC-invariant).
- **PRO is NOT computed by the released code**. README: "_>95%_ PRO score (although the later metric is not included for license reasons)". Open issues #26 and #53 ask for the PRO code (unanswered); #26 reports **92.9** with RD4AD's `compute_pro` vs released 94.9 for the ensemble.
- **Published results CSVs** (in repo, `models/*/results.csv`, read today) contain columns `instance_auroc, full_pixel_auroc, full_pro, anomaly_pixel_auroc, anomaly_pro`. README table "Mean PRO 94.4 % (WR50) / 94.9 % (Ensemble)" corresponds to the **`anomaly_pro`** column (anomalous test images only; code comment "Compute PRO score & PW Auroc only images with anomalies"); `full_pro` (all test images) is only **0.684 / 0.684**, which is implausibly low vs. the official definition and indicates their internal PRO differs from the official one **[INFERRED]**. → **PatchCore's published PRO numbers are not comparable to official AU-PRO@0.3.**
  - WR50 baseline (IM224, P0.1): mean instance AUROC 0.9916, full pixel AUROC 0.9811, anomaly_pro 0.9437. Per-category values stored in our search notes (transistor anomaly_pro 0.832, tile 0.898, wood 0.902 lowest).
  - Ensemble IM224 (WRN101+ResNeXt101+DenseNet201, P0.01): 0.9934 / 0.9813 / 0.9433; IM320 ensemble: 0.9955 / 0.9823 / 0.9493.
- **Paper (CVPR 2022, DOI 10.1109/CVPR52688.2022.01392, pp. 14298–14308)**: Table 1 image AUROC PatchCore-25/10/1 % = 99.1/99.0/99.0; Table 2 pixel AUROC 98.1/98.1/98.0; Table 3 PRO 93.5 (−25 %) vs PaDiM 92.1, SPADE 91.7; PRO "following [6]" (= Uninformed Students). Eval: "resized and center cropped to 256 × 256 and 224 × 224".
- **Dependencies** (`requirements.txt`): click, faiss-cpu (faiss-gpu commented), matplotlib, pillow, **pretrainedmodels≥0.7.4**, torch≥1.10, scikit-image, scikit-learn, scipy, torchvision≥0.11.1, tqdm; Python 3.8. PyPI today: faiss-cpu 1.15.1 (py≥3.10), faiss-gpu-cu12 1.14.1.post1 wheels cp310–cp313. **[UNRESOLVED/Colab risk]** `pretrained=True` torchvision API and the unmaintained `pretrainedmodels` package on current Colab Python — test in Phase 1 (PatchCore only needs `pretrainedmodels` for non-torchvision backbones).

**anomalib** (repo moved to https://github.com/open-edge-platform/anomalib; Apache-2.0; latest release lib/v2.7.0, 2026-10-06; PyPI anomalib 2.7.0):
- PatchCore defaults: `wide_resnet50_2`, layers (layer2, layer3), coreset 0.1, `num_neighbors=9` (used for the paper's re-weighting), pre-processor Resize(256,256)+CenterCrop(224,224), Gaussian sigma=4; NN search in torch (no faiss). README benchmark (seed 42): **image AUROC avg 0.980**, pixel AUROC 0.980 (WR50) — lower than official 0.992/0.981 (e.g. toothbrush 0.933, pill 0.924, screw 0.960). No AU-PRO in README.
- **AUPRO implementation history** (verified): before PR #3115 (merged 2025-11-18, "Speedup AUPRO") anomalib computed a per-region ROC with binned curves and normalised by `fpr[-1]` (endpoint of averaged curve), not by the limit. Issue #3718 (user report, 2026-08-12) quantifies vs official script on AUPIMO-released maps: PatchCore/bottle −0.012 pp, **EfficientAD-M/bottle +1.83 pp, tile −0.85 pp, grid 1.36 (>1, impossible)**; issue #1651 (2024) reported AU-PRO = 1.21; also torchmetrics applies a sigmoid when preds outside [0,1]. Current `main` (`metrics/aupro.py`) re-implements the MVTec global-sort algorithm with interpolation at `fpr_limit`, but still returns `auc/fpr[-1]` (issue #3718 asks whether a residual branch is reachable) **[UNRESOLVED; issue open]**. Connectivity: CPU path `cv2.connectedComponents` (default 8-connectivity); GPU path kornia `connected_components` (3×3 max-pool propagation = 8-connectivity, iterative with `num_iterations=1000` — may under-merge very long components) [INFERRED FROM CODE].
- **RD4AD `compute_pro`** (widely copied; https://github.com/hq-deng/RD4AD/blob/main/test.py): 200 uniform thresholds between min/max, per-region overlap with `skimage.measure.label` (default full connectivity = 8 in 2D), keeps points with FPR<0.3 and then **rescales FPR by its max** (not by 0.3) → not identical to official. Use neither.

**Known implementation discrepancies to pre-register**: (i) center-crop vs full image; (ii) GT down-sampling and binarisation; (iii) PRO normaliser (0.3 vs last FPR) and binned vs exact thresholds; (iv) PRO on anomalous-only images vs all test images (PatchCore's `anomaly_pro`); (v) image score max vs mean-of-top-k; (vi) anomalib k=9 re-weighting vs official num_nn=1.

### A4. Evaluation bias vs defect size; benchmark critiques; conventions

| Source (verified) | Finding relevant to size bias |
|---|---|
| IJCV 2021 (Bergmann et al.) | PRO introduced so small regions count equally; pixel-level metrics dominated by large regions; integration limit choice changes rankings. |
| MVTec LOCO "Beyond Dents and Scratches", IJCV 130:947–969 (2022), DOI 10.1007/s11263-022-01578-9 | Introduces **sPRO** (saturated PRO): sPRO(P) = (1/m) Σ_i min(|A_i ∩ P| / s_i, 1), saturation thresholds s_i ≤ |A_i| shipped with the dataset; used for logical anomalies. **[SECONDARY]** — formula from search snippet; Springer full text inaccessible today; SAM-LAD (arXiv 2406.00625) confirms "saturated Per-Region Overlap ... reaches saturation once it overlaps with the ground truth and achieves a predefined saturation threshold. All thresholds are also provided by the MVTec LOCO AD dataset", used at FPR 5 %. Not applicable to MVTec AD (no thresholds provided). |
| MVTec AD 2 (arXiv 2503.21622; IJCV 2026, DOI 10.1007/s11263-026-02743-0) | Fig. 4: "PRO considers each anomalous region equally, whereas the TPR is dominated by large defects and overestimates defect localization quality"; adopts **AU-PRO@0.05** ("for a defect size of 10 pixels in a 5MP image, even a FPR of 5% ... results in a wrongly segmented area that is more than 25,000 times larger than the defect itself"); also thresholded pixel F1 (SegF1) on private test set; criticises test-set tuning and approximated AU-PRO variants. |
| AUPIMO (Bertoldo et al., arXiv 2401.01984, BMVC 2024; code MIT https://github.com/jpcbertoldo/aupimo; in anomalib) | Per-image overlap curves, FPR axis from **normal images only**, very low FPR tolerance; robust to noisy annotations; enables statistical tests; argues MVTec AD/VisA not "solved". Released score maps on Zenodo 10523601. |
| Zheng et al. 2022 (arXiv 2205.14852) | Saturation; label ambiguity in MVTec AD. |
| Baitieva et al., CVPRW 2025 (arXiv 2503.23451, DOI 10.1109/CVPRW67362.2025.00386; code Apache-2.0 abc-125/viad-benchmark) | Real-production datasets; practical metrics; academic benchmarks misdirect. |
| Röchner et al. 2025 (arXiv 2507.15584) "We Need to Rethink Benchmarking in Anomaly Detection" | Position paper on evaluation-driven stagnation (general AD). |
| Deng 2026 (arXiv 2608.15090) | Distribution-free false-alarm thresholds + chance-corrected spatial overlap; shows raw mask overlap can be inflated by recurrent defect locations — relevant critique for overlap metrics. |
| Hermary et al. 2026 (arXiv 2607.22286, EUVIP 2026) | Metric behaviour under imbalance (AUROC/AUPR/F1/MCC). |
| IM-IAD (Xie et al., arXiv 2301.13359; IEEE T-Cybernetics 54:2720–2733, DOI 10.1109/TCYB.2024.3357213; code M-3LAB/IM-IAD, no licence file) | Uniform benchmark, 19 algorithms, 7 datasets. |
| Real-IAD (CVPR 2024, arXiv 2403.12580, DOI 10.1109/CVPR52733.2024.02159) | New dataset; MVTec AD 2 notes unsupervised models already at 94.4 % AU-PRO@0.3 on it. |
| ADBench (NeurIPS 2022 D&B, arXiv 2206.09426) | **Tabular** AD benchmark — not relevant to pixel-level MVTec protocol; do not cite as image-AD evidence. |
| "Rethinking evaluation of industrial anomaly detection" (exact title) | **[UNRESOLVED]** — no paper with this title found; the closest are 2503.23451 and 2507.15584. |
| Size-stratified evaluation on MVTec AD | **No paper found** that reports official-metric results stratified by GT-component area on MVTec AD (searches 43–48 in log). Sequential PatchCore (arXiv 2501.09579) reports "defect-wise recall" on a private surface dataset; SegmentMeIfYouCan (NeurIPS 2021 D&B) uses component-level metrics for road scenes. → size-stratified PRO decomposition is a **gap / contribution opportunity**. |

**Standard conventions (consensus as of today)**: per-category image AUROC (max-map score) and per-category AU-PRO@0.3 (official code), averaged over 15 categories; pixel AUROC widely reported but recognised as large-defect-biased and saturated; AU-PRO@0.05 (MVTec AD 2) and AUPIMO emerging for low-FPR regimes; sPRO only for LOCO.

---

#### B. BASELINES / COMPARATORS

### B5. PatchCore official — feasibility
- Weights: torchvision `wide_resnet50_2(pretrained=True)` → ImageNet-1k pretrained weights (no ImageNet images needed). EfficientAD/PatchCore-Ens use WRN-101 / ResNeXt-101 / DenseNet-201 (ensemble via `pretrainedmodels`).
- faiss: `faiss-cpu` in requirements; `--faiss_on_gpu` optional. On Colab, faiss-cpu is sufficient at 1–10 % coreset; full memory bank (100 %) exact search for 391 hazelnut images × 28×28 patches ≈ 306k vectors × 1024-d float32 ≈ 1.25 GB — feasible on Colab RAM with faiss-cpu/flat; GPU flat search requires faiss-gpu-cu12 wheel. [estimate, not measured]
- Licence Apache-2.0; ships pre-trained models + results.csv (useful as reproduction targets for instance AUROC/pixel AUROC only).

### B6. EfficientAD (arXiv 2303.14535; WACV 2024 pp. 128–138 per CVF/MVTec; S2/IEEE metadata lists pp. 127–137, DOI 10.1109/WACV57701.2024.00020 — page discrepancy noted)
- **Official code: none found.** arXiv abs page has no code link; CVF BibTeX/HTML has no code link; MVTec publications page lists only the PDF; all GitHub implementations self-describe as unofficial (nelson1425, cinout, mjack3, rximg, dellysursh …).
- **ImageNet dependency (paper text)**: §3.1 "We train the PDN on images from ImageNet by minimizing the mean squared difference between its output and the features extracted from the pretrained network" (WRN-101 PatchCore features, App. A.2: batch 16, ImageNet); §3.2 penalty: "we sample a random image P from the pretraining dataset, in our case ImageNet, in each training step", L_ST = L_hard + mean‖S(P)‖². Ablation (Table 5): without pretraining penalty −0.4 pp (avg of MVTec AD/VisA/LOCO means, EfficientAD-S).
- **Evaluation in the paper**: AU-ROC image, AU-PRO@0.3 using official scripts; PatchCore re-run **without center crop** ("we disable the cropping of the center 76.6 % of input images for a fair comparison ... it implies knowledge about the anomalies in the test set"). MVTec AD means (Table 10/12): EfficientAD-S 98.8 / 93.1 AU-PRO, -M 99.1 / 93.5; their uncropped PatchCore 92.7 AU-PRO, PatchCore-Ens 95.6. Per-scenario results JSON (200 KB) at MVTec mydrive (footnote 10), not downloaded.
- **nelson1425/EfficientAD** (Apache-2.0, last push 2023-08-03): "Unofficial implementation"; README: MVTec AD M 99.1 (paper 99.1), S 99.0 (paper 98.8); "Reproducing results from paper requires ImageNet stored somewhere"; `--imagenet_train_path none` disables the penalty; ships `models/teacher_{small,medium}.pth` (teacher distilled by the repo author, `pretraining.py` uses WRN-101 IMAGENET1K_V1 on ImageNet train); 70,000 steps; random 90/10 train/val split of the good training images for map normalisation; evaluates with official MVTec scripts.
- **anomalib EfficientAd**: "based on rximg/EfficientAd and nelson1425/EfficientAd"; penalty set = **Imagenette** (`imagenette2.tgz` auto-download) instead of ImageNet; teacher weights auto-downloaded from an anomalib GitHub release; README image AUROC (seed 42): S **0.982**, M **0.975** (paper 98.8/99.1) — not an exact reproduction.
- **Verdict**: exact, licence-clean reproduction without ImageNet = **not feasible**. Compliant alternative = run anomalib/nelson variant clearly labelled as approximate, or omit and cite paper numbers (computed with official script, no crop — directly comparable to our frozen protocol).

### B7. Memory/density normal-only comparators

See matrix (§D). Summary: PaDiM — no official code (only unofficial xiahaifeng1995 Apache-2.0, and anomalib); SPADE — no official code found (byungjae89 Apache-2.0 unofficial); CFA — official code (sungwool), **no licence file**, trains a patch descriptor; GraphCore — no code found; PNI — official code (wogur110), **no licence file**, includes a pixel-wise refinement net trained on synthetic defects + faiss; SoftPatch — official (TencentYoutuResearch), **no licence file**, PatchCore-based noise-robust variant; CPR — official MIT, retrieval + trained refinement, 97.8 % AU-PRO; AnomalyDINO — official Apache-2.0, training-free DINOv2 patch kNN, includes an evaluation script that "partly builds on the official evaluation script for MVTec-AD".

### B8. Small-defect related
- No method found that specifically claims improved small/tiny-defect performance on **MVTec AD** with a size-stratified evaluation. Related: MVTec AD 2 (dataset for small defects; AU-PRO@0.05), Divide-and-Conquer tiled ensemble (Rolih et al., CVPRW 2024, arXiv 2403.04932 — high-resolution for small defects, anomalib), PatchCore's own higher-resolution runs (IM320), Sequential PatchCore (defect-wise recall, private data), "What Memory Composition Does Not Tell Us About Anomaly Detection" (arXiv 2608.23295, 2026-08-24: compares **random, medoid, local and global-coverage memory selectors under fixed budgets**; finds global coverage over-represents contamination; lowest-contamination memory ≠ best P-AP) — **closest related/possible-scoop work for this project; read in full in Phase 1**. Also ProCon (arXiv 2607.04894, training-free soft projection memory, claims 99.8 % image AUROC MVTec AD; code no licence), Mahalanobis PatchCore (arXiv 2605.27748, streaming memory, peak memory 5.41→2.78 GB), Training-free HITL memory-bank correction (arXiv 2608.17775), contamination-aware DINOv2 memory banks (arXiv 2608.22082), Optimizing PatchCore for few/many-shot (arXiv 2307.10792).

#### C. SOTA census (successor to Papers-with-Code)
- `paperswithcode.com/sota/anomaly-detection-on-mvtec-ad` now **302-redirects to huggingface.co/papers/trending** (checked today). PwC retired July 2025 (per CodeSOTA page; **[SECONDARY]**).
- CodeSOTA (https://www.codesota.com/benchmark/mvtec-ad): image AUROC only; SimpleNet 99.6, FastFlow 99.4, PatchCore 99.1, EfficientAD 99.1, RD 98.5, CFLOW 98.3, DRAEM 98.0, PaDiM 97.9 — scraped from PwC/arXiv, **no PRO, no protocol control** (SimpleNet 99.6 uses per-category training-length selection on test per EfficientAD App. B.6). Not citable as evidence.
- tomomi-research SOTA viewer: no PRO table; notes values hand-collected as of 2026-09-01.
- anomalib per-model README tables (seed 42, image AUROC/pixel AUROC/F1, no AU-PRO) — consistent pipeline, but numbers below official papers.
- **Training-free / memory-based numbers on MVTec AD (from primary papers, verified)**:

| Method | Image AUROC | Pixel AUROC | PRO / AU-PRO | Protocol note |
|---|---|---|---|---|
| SPADE (arXiv 2005.02357) | 85.5 | 96.0 | 91.7 (PRO) | as reported in SPADE Tables 1–3 |
| PaDiM WR50-Rd550 (ICPRW 2020) | 95.3 (97.9 w/ EfficientNet-B5) | 97.5 | 92.1 | PaDiM Tables III/V |
| PatchCore-25 % / 10 % / 1 % (CVPR 2022) | 99.1 / 99.0 / 99.0 | 98.1 / 98.1 / 98.0 | 93.5 (−25 %) | 224 center crop; PRO impl. unreleased |
| PatchCore WR50 official results.csv | 99.16 | 98.11 | 94.4 (anomaly-only images) | 224 crop |
| PatchCore (EfficientAD re-run, no crop) | – | – | 92.7 AU-PRO@0.3 | official MVTec script |
| PatchCore-Ens (EfficientAD re-run, no crop) | – | – | 95.6 | official script |
| CPR (TIP 2024) | – | – | 97.8 (per MVTec AD 2 paper) | uses trained refinement — not training-free |
| PNI (ICCV 2023) README | 99.56 | 98.98 | 96.05 | trained refinement net; ensemble 99.63/99.06/96.55 |
| CFA (IEEE Access 2022) | 99.3 | 98.2 | – | trained feature adaptation |
| ProCon (arXiv 2607.04894, 2026) | 99.8 | – | – (claims 7 metrics) | preprint, unreviewed |

---

#### D. Paper matrix

| Paper (venue, year, verified URL) | Problem | Method family | Benchmark(s) | Headline number | Code? (URL, official?, licence) | Notes for protocol |
|---|---|---|---|---|---|---|
| Bergmann et al., MVTec AD (CVPR 2019) https://openaccess.thecvf.com/content_CVPR_2019/papers/Bergmann_MVTec_AD_--_A_Comprehensive_Real-World_Dataset_for_Unsupervised_Anomaly_CVPR_2019_paper.pdf | Dataset | Benchmark | MVTec AD | 5354 imgs, 1888 regions | Eval code via MVTec page (BSD-3-style, ©MVTec) | Single-threshold PRO in 2019 version; AU-PRO@0.3 in IJCV |
| Bergmann et al., IJCV 129 (2021) DOI 10.1007/s11263-020-01400-4 (OA copy https://d-nb.info/1226611842/34) | Dataset + metrics | Benchmark | MVTec AD | AU-PRO@0.3 normalised; 2.7 % anomalous pixels | same | Canonical PRO definition (Eq. 9); limits 0.01/0.05/0.3/1.0 discussed |
| Bergmann et al., Uninformed Students (CVPR 2020) arXiv 1911.02357, DOI 10.1109/CVPR42600.2020.00424 | Localisation | S–T | MVTec AD | – | none checked | First explicit "until avg per-pixel FPR 30 %, normalise to 1" |
| Bergmann et al., MVTec LOCO "Beyond Dents and Scratches" (IJCV 130, 2022) DOI 10.1007/s11263-022-01578-9 | Logical anomalies | Benchmark/GCAD | MVTec LOCO | sPRO | LOCO eval code (MVTec) | sPRO [SECONDARY]; not for MVTec AD |
| Heckler-Kram et al., MVTec AD 2 (IJCV 2026) arXiv 2503.21622, DOI 10.1007/s11263-026-02743-0 | Harder dataset | Benchmark | MVTec AD 2 | SOTA ≤58.7 % AU-PRO@0.3 | – | AU-PRO@0.05; TPR large-defect bias (Fig. 4); anti test-tuning |
| Roth et al., PatchCore (CVPR 2022) arXiv 2106.08265, DOI 10.1109/CVPR52688.2022.01392 | AD+AS | Memory bank + greedy coreset kNN | MVTec AD, mSTC | 99.1 img AUROC, 98.1 px, 93.5 PRO | https://github.com/amazon-science/patchcore-inspection official, Apache-2.0 | 256→224 crop; σ=4; PRO code withheld; anomaly-only PRO in CSV |
| Batzner et al., EfficientAD (WACV 2024) arXiv 2303.14535, DOI 10.1109/WACV57701.2024.00020 | Fast AD | S–T + AE | MVTec AD, VisA, LOCO | MAD: 99.1 / 93.5 AU-PRO (M) | **No official**; nelson1425 unofficial Apache-2.0; anomalib Apache-2.0 | Needs ImageNet (distillation + penalty); disables crop for fairness |
| Defard et al., PaDiM (ICPR Workshops 2020) arXiv 2011.08785, DOI 10.1007/978-3-030-68799-1_35 | AD+AS | Per-position Gaussian | MVTec AD, STC | 95.3 img / 97.5 px / 92.1 PRO (WR50) | No official; xiahaifeng1995 (unofficial, Apache-2.0); anomalib | Density baseline, training-free |
| Cohen & Hoshen, SPADE (arXiv 2005.02357, 2020) | AD+AS | kNN image + pyramid patch kNN | MVTec AD, STC | 85.5 img / 96.0 px / 91.7 PRO | No official found; byungjae89/SPADE-pytorch (unofficial, Apache-2.0) | Uncompressed memory baseline; arXiv-only (S2 venue arXiv) |
| Lee et al., CFA (IEEE Access 10, 2022) arXiv 2206.04325 | AS | Memory + trained patch descriptor (hypersphere) | MVTec AD | 99.3 img / 98.2 px | sungwool/CFA_for_anomaly_localization official, **no licence file** | Not training-free |
| Xie et al., GraphCore (ICLR 2023) arXiv 2301.12082 | Few-shot AD | Memory + GNN rotation-invariant features | MVTec AD, MPDD | few-shot | **No code found** | Few-shot; cite only |
| Bae et al., PNI (ICCV 2023) arXiv 2211.12634, DOI 10.1109/ICCV51070.2023.00586 | AD+AS | Memory + position/neighbourhood distributions + refinement | MVTec AD, VisA, BTAD | 99.56 / 98.98 / 96.05 AUPRO | wogur110/PNI_anomaly_detection official, **no licence file**, faiss-gpu 1.7 | Refinement net trained on synthetic defects |
| Jiang et al., SoftPatch (NeurIPS 2022) arXiv 2403.14233 | Noisy training data | PatchCore + patch-level denoising | MVTec AD, BTAD | README I/P AUROC per class | TencentYoutuResearch/AnomalyDetection-SoftPatch official, **no licence file** | Memory composition / contamination |
| Wang et al., SoftPatch+ (Pattern Recognition 2024) arXiv 2412.20870, DOI 10.1016/j.patcog.2024.111295 | Fully unsupervised | as above | – | – | same repo | – |
| Li et al., CPR (IEEE TIP 33:5606–5621, 2024) arXiv 2308.06748, DOI 10.1109/TIP.2024.3448263 | Fast AD+AS | Cascade patch retrieval + refinement | MVTec AD etc. | 97.8 AU-PRO (cited by MVTec AD 2) | flyinghu123/CPR official, MIT | Trained components |
| Damm et al., AnomalyDINO (WACV 2025) arXiv 2405.14529, DOI 10.1109/WACV61041.2025.00136 | Few-shot AD | DINOv2 patch kNN, training-free | MVTec AD, VisA | – (not extracted) | dammsi/AnomalyDINO official, Apache-2.0 | Eval script built on official MVTec script |
| Bertoldo et al., AUPIMO (BMVC 2024) arXiv 2401.01984 | Metric | Per-image overlap | MVTec AD, VisA | – | jpcbertoldo/aupimo official, MIT; in anomalib | Low-FPR, per-image, statistical tests |
| Zheng et al., Benchmarking UAD&L (arXiv 2205.14852, 2022) | Benchmark | survey/benchmark | MVTec AD, 3D-AD | – | – | Label ambiguity examples |
| Xie et al., IM-IAD (IEEE T-Cyb 54, 2024) arXiv 2301.13359, DOI 10.1109/TCYB.2024.3357213 | Benchmark | 19 algorithms | 7 datasets | – | M-3LAB/IM-IAD, no licence file | Uniform settings |
| Wang et al., Real-IAD (CVPR 2024) arXiv 2403.12580, DOI 10.1109/CVPR52733.2024.02159 | Dataset | Benchmark | Real-IAD | – | – | – |
| Baitieva et al., Beyond Academic Benchmarks (CVPRW 2025) arXiv 2503.23451, DOI 10.1109/CVPRW67362.2025.00386 | Benchmark critique | – | real production data | – | abc-125/viad-benchmark, Apache-2.0 | Practical metrics |
| Röchner et al., We Need to Rethink Benchmarking in AD (arXiv 2507.15584, 2025) | Benchmark critique | – | general AD | – | – | Position paper |
| Rolih et al., Divide and Conquer tiled ensemble (CVPRW 2024 VAND) arXiv 2403.04932 | High-res AD | Tiled ensemble | MVTec AD, VisA | – | in anomalib (Apache-2.0) | Small defects via resolution |
| Bergmann et al., MVTec 3D-AD (VISAPP 2022) arXiv 2112.09045, DOI 10.5220/0010865000003124 | Dataset | – | 3D-AD | – | – | Recommends AU-PRO limit ≤0.3 [SECONDARY via search snippet] |
| Chae et al., What Memory Composition Does Not Tell Us (arXiv 2608.23295, 2026) | Memory selection | Coreset selector comparison | (12 matched comparisons; datasets not extracted) | P-AP | – | **Closest related work**; check full text |
| Chae et al., ProCon (arXiv 2607.04894, 2026) | Training-free AD | Soft projection on memory | MVTec AD, VisA, Real-IAD | 99.8 img AUROC MAD | jw-chae/Procon, no licence file | Preprint |
| Ferrari et al., Mahalanobis PatchCore (arXiv 2605.27748, 2026) | Memory-efficient | Whitened kNN, streaming | MVTec AD + 3 private | peak mem 5.41→2.78 GB | – | Preprint |
| Abbas et al., HITL memory-bank correction (arXiv 2608.17775, 2026) | Bank editing | PatchCore | MVTec AD | – | – | Warns naive eval inflates via memorisation |
| Santos et al., Optimizing PatchCore few/many-shot (arXiv 2307.10792, 2023) | Hyper-params | PatchCore | MVTec AD, VisA | – | – | Backbone matters most |
| Mao et al., Sequential PatchCore (arXiv 2501.09579, 2025) | High-res memory | Sequential coreset | synthetic/real surfaces | defect-wise recall | – | Defect-wise recall precedent |
| Kalantary & Khoramdel (arXiv 2608.22082, 2026) | Memory contamination | DINOv2 bank + greedy coreset | Severstal | AUPRC | – | Budget-matched memory comparisons |

---


## F. Unresolved / caveats list
1. Official eval tarball version (1.0 in mirror vs "v2.0" in anomalib issue #3718) — needs a tarball diff (not downloaded).
2. sPRO formula — only secondary verification (Springer blocked).
3. EfficientAD WACV pages 128–138 (CVF, MVTec) vs 127–137 (IEEE/S2).
4. GraphCore official code — none found.
5. "Rethinking evaluation of industrial anomaly detection" exact-title paper — not found.
6. PatchCore `full_pro` (0.684) vs `anomaly_pro` (0.944) semantics — inferred from code comments; PRO code itself unreleased.
7. anomalib current AUPRO residual normaliser issue (#3718) — open.
8. Colab compatibility of `pretrainedmodels` / `pretrained=True` — untested.
9. MVTec defect-folder names (transistor/misplaced, metal_nut/flip) are from secondary snippets, not paper text.
10. No published size-stratified MVTec AD evaluation found (absence of evidence after 6 targeted searches, not proof).

---

#### G. SEARCH LOG (all 2026-10-11)

| # | date | engine | query | n relevant | notable |
|---|---|---|---|---|---|
| 1 | 2026-10-11 | WebFetch | mvtec.com/research-teaching/datasets/mvtec-ad | 1 | CC BY-NC-SA 4.0; eval code exists |
| 2 | 2026-10-11 | WebFetch | github.com/amazon-science/patchcore-inspection | 1 | Apache-2.0; PRO excluded "for license reasons" |
| 3 | 2026-10-11 | WebFetch | arxiv.org/abs/2303.14535 | 1 | v3, WACV 2024 pp.128-138; no code link |
| 4 | 2026-10-11 | WebFetch | github.com/nelson1425/EfficientAD | 1 | "Unofficial"; ImageNet required |
| 5 | 2026-10-11 | WebFetch | raw PatchCore README | 1 | (summarised; re-fetched via curl #9) |
| 6 | 2026-10-11 | WebFetch | raw patchcore metrics.py | 1 | no PRO function |
| 7 | 2026-10-11 | WebFetch | raw patchcore common.py | 1 | bilinear + gaussian σ=4 |
| 8 | 2026-10-11 | WebFetch | raw patchcore requirements.txt | 1 | faiss-cpu, pretrainedmodels |
| 9 | 2026-10-11 | curl | raw PatchCore README.md | 1 | full text; results table 94.4/94.9 PRO |
| 10 | 2026-10-11 | GitHub API | patchcore repo tree + 6 results.csv | 6 | full_pro vs anomaly_pro columns |
| 11 | 2026-10-11 | curl | run_patchcore.py, datasets/mvtec.py, backbones.py, patchcore.py | 4 | crop applied to masks; anomaly-only metrics |
| 12 | 2026-10-11 | WebFetch | link.springer.com IJCV article | 0 | 303 redirect to login |
| 13 | 2026-10-11 | Semantic Scholar API | DOI:10.1007/s11263-020-01400-4 | 1 | IJCV 129:1038-1059, OA CC BY |
| 14 | 2026-10-11 | curl | Springer PDF / HTML | 0 | blocked |
| 15 | 2026-10-11 | curl | CVPR 2019 openaccess PDF | 1 | Table 1 counts |
| 16 | 2026-10-11 | WebSearch | mvtec_ad_evaluation generic_util.py compute_pro integration_limit 0.3 github | 3 | pointers to mirrors |
| 17 | 2026-10-11 | WebSearch | "The MVTec Anomaly Detection Dataset" IJCV 2021 PRO metric integration limit 0.3 connected components | 3 | d-nb.info OA copy |
| 18 | 2026-10-11 | WebSearch | MVTec AD label errors ground truth issues mislabeled | 2 | no errata found |
| 19 | 2026-10-11 | curl | d-nb.info/1226611842/34 (IJCV OA PDF) | 1 | PRO Eq.9, 0.3 limit, annotation policy, Table 1 |
| 20 | 2026-10-11 | gh search code | "def compute_pro" "integration_limit" | 15 | many vendored copies |
| 21 | 2026-10-11 | GitHub API | tootouch/MemSeg pro_curve_util.py, generic_util.py; dammsi/AnomalyDINO post_eval.py | 3 | 8-connectivity, exact thresholds |
| 22 | 2026-10-11 | gh search code | "pro_integration_limit" "evaluate_experiment"; "MVTec Software GmbH" | 10 | mirrors of official code |
| 23 | 2026-10-11 | GitHub API | Sam-khanjani/AnomalyDetection mvtec_ad_evaluation README/LICENSE/evaluate_experiment.py | 1 | BSD-3-style licence; version 1.0; np.max image score |
| 24 | 2026-10-11 | GitHub API | nelson1425/EfficientAD meta/tree/README/pretraining.py/efficientad.py | 1 | teacher weights; penalty; 90/10 split |
| 25 | 2026-10-11 | curl | arxiv.org/pdf/2303.14535v3 | 1 | ImageNet in distillation + penalty; crop disabled |
| 26 | 2026-10-11 | curl -I | EfficientAD per_scenario_results.json (headers only) | 1 | exists, 200 KB, not downloaded |
| 27 | 2026-10-11 | GitHub API/curl | anomalib tree, metrics/aupro.py, pro.py, utils/cv/connected_components.py, kornia cc, PR #3115 | 5 | exact algorithm since 2025-11 |
| 28 | 2026-10-11 | gh search issues | AUPRO in open-edge-platform/anomalib; issues #3718, #1651 | 3 | normaliser bug quantified |
| 29 | 2026-10-11 | curl | anomalib patchcore README, lightning_model, anomaly_map, torch_model | 4 | img AUROC 0.980; k=9; crop 224 |
| 30 | 2026-10-11 | curl | anomalib efficient_ad README + lightning_model | 2 | Imagenette; S .982 / M .975 |
| 31 | 2026-10-11 | WebSearch | EfficientAD official implementation code MVTec Batzner Heckler König released | 6 | only unofficial repos |
| 32 | 2026-10-11 | WebSearch | EfficientAD WACV 2024 openaccess.thecvf.com Batzner ... | 3 | CVF page |
| 33 | 2026-10-11 | WebFetch/curl | CVF EfficientAD html (403 via WebFetch; curl OK), MVTec publications page | 2 | BibTeX; no code link |
| 34 | 2026-10-11 | WebSearch | mvtec.com research publications EfficientAD code availability HALCON | 1 | no code |
| 35 | 2026-10-11 | WebSearch | anomaly segmentation evaluation bias defect size AU-PRO pixel AUROC large defects dominate small defects MVTec | 2 | general statements |
| 36 | 2026-10-11 | WebSearch | AUPIMO per-image overlap anomaly detection benchmark arXiv 2401.01984 | 3 | AUPIMO, Zenodo maps |
| 37 | 2026-10-11 | WebSearch | rethinking evaluation industrial anomaly detection benchmark critique metrics 2024 2025 arXiv | 5 | 2503.23451, 2507.15584, 2608.15090, 2607.22286 |
| 38 | 2026-10-11 | arXiv API | id_list (21 IDs: 1911.02357 … 2405.14529) | 21 | metadata/venues |
| 39 | 2026-10-11 | curl | arxiv.org/pdf/2503.21622 (MVTec AD 2) | 1 | AU-PRO@0.05; TPR bias; 97.8 % SOTA |
| 40 | 2026-10-11 | Semantic Scholar API | DOIs LOCO, CVPR19, PatchCore, EfficientAD | 4 | DOIs/pages |
| 41 | 2026-10-11 | WebSearch | "saturated per-region overlap" sPRO saturation threshold MVTec LOCO definition | 2 | sPRO formula (snippet) |
| 42 | 2026-10-11 | WebFetch/curl | arXiv 2406.00625 abs + PDF | 1 | sPRO secondary confirmation |
| 43 | 2026-10-11 | WebSearch | small defect tiny anomaly detection MVTec AD unsupervised improve small anomalies localization arXiv | 1 | nothing specific |
| 44 | 2026-10-11 | WebSearch | PatchCore coreset subsampling ratio small defects memory bank compression anomaly detection analysis | 3 | 2307.10792, 2608.17775, SoftPatch+ |
| 45 | 2026-10-11 | WebSearch | anomaly detection evaluation stratified by defect size MVTec AD per-defect-size analysis region area | 0 | none |
| 46 | 2026-10-11 | WebSearch | SoftPatch unsupervised anomaly detection with noisy data NeurIPS 2022 github code | 3 | official repo; 2608.23295 found |
| 47 | 2026-10-11 | WebSearch | "small defects" OR "tiny defects" anomaly detection high-resolution patch memory MVTec AD 2025 2026 arXiv method | 2 | 2403.04932, 2607.04894 |
| 48 | 2026-10-11 | WebSearch | "size-aware" OR "size-stratified" anomaly segmentation evaluation small anomalies metric industrial | 1 | SegmentMeIfYouCan component metrics |
| 49 | 2026-10-11 | arXiv API | 11 IDs (2608.23295, 2607.04894, 2608.17775, 2403.04932, …) + abstracts | 11 | memory-composition paper |
| 50 | 2026-10-11 | arXiv API | abstracts 2605.27748, 2307.10792, 2503.23451, 2608.15090, 2607.22286, 2401.01984, 2205.14852, 2301.13359 | 8 | – |
| 51 | 2026-10-11 | WebSearch | MVTec AD annotation errors "ground truth" noisy masks relabel "MVTec AD" corrected labels study | 0 | no relabel study |
| 52 | 2026-10-11 | WebSearch | MVTec AD transistor "misplaced" metal_nut "flip" logical anomalies image-level only ambiguity | 1 | secondary only |
| 53 | 2026-10-11 | curl | arxiv.org/pdf/2205.14852 | 1 | label ambiguity examples |
| 54 | 2026-10-11 | GitHub API | licences of 12 comparator repos | 12 | CFA/PNI/SoftPatch/ProCon/IM-IAD no licence |
| 55 | 2026-10-11 | GitHub API | root listings + READMEs (SoftPatch, PNI) | 4 | PNI 99.56/98.98/96.05 |
| 56 | 2026-10-11 | curl | arXiv PDFs 2011.08785, 2005.02357, 2206.04325, 2106.08265 | 4 | headline numbers |
| 57 | 2026-10-11 | curl | arxiv.org/pdf/1911.02357 | 1 | 30 % FPR, normalise to 1 |
| 58 | 2026-10-11 | WebSearch | Papers with Code shut down successor leaderboard anomaly detection MVTec AD SOTA 2026 | 3 | CodeSOTA |
| 59 | 2026-10-11 | WebFetch | paperswithcode.com/sota/anomaly-detection-on-mvtec-ad | 0 | 302 → huggingface.co/papers/trending |
| 60 | 2026-10-11 | WebFetch | codesota.com/benchmark/mvtec-ad | 1 | image AUROC only |
| 61 | 2026-10-11 | WebFetch | tomomi-research.com/en/ad-sota-eng | 0 | no PRO table |
| 62 | 2026-10-11 | Semantic Scholar API | batch of 17 arXiv IDs | 16 | venues/DOIs |
| 63 | 2026-10-11 | WebSearch | memory bank coreset compression anomaly detection defect size small anomalies recall trade-off 2026 arXiv PatchCore | 3 | 2608.22082, 2501.09579 |
| 64 | 2026-10-11 | WebSearch | GraphCore few-shot anomaly detection ICLR 2023 official code github | 0 | no code |
| 65 | 2026-10-11 | arXiv API + curl | 2501.09579, 2608.22082 abstracts; GraphCore PDF code grep | 3 | GraphCore no code link |
| 66 | 2026-10-11 | curl | MVTec AD page links | 1 | current eval tarball URL; licence |
| 67 | 2026-10-11 | PyPI JSON API | faiss-cpu, faiss-gpu, faiss-gpu-cu12, anomalib, timm | 5 | versions for Colab |
| 68 | 2026-10-11 | gh search issues + gh issue view | patchcore-inspection "PRO" (#26, #53), "center crop" (#5) | 3 | RD4AD PRO gives 92.9 vs 94.9 |
| 69 | 2026-10-11 | curl | RD4AD test.py compute_pro | 1 | binned, renormalised by max FPR |
| 70 | 2026-10-11 | GitHub API | patchcore-inspection commits | 1 | last commit 2023-03-06 |


---

## Appendix C — venue pass C, 2026-10-11, full record

### Venue verification: Pattern Recognition vs Neurocomputing (Elsevier)

Date of all checks: 2026-10-11 (live fetches only). Verification grade legend:
- **V-primary** = read directly from publisher / Crossref / CTAN / Clarivate-cited source.
- **V-snippet** = only seen in a web-search snippet that quotes the official page (page itself returned 403). Treat as likely but re-check by hand.
- **U** = unverified / conflicting.

#### 1. Search log

| # | date | query / URL | result |
|---|------|-------------|--------|
| 1 | 2026-10-11 | api.crossref.org/works?query.title=MMFNet multi-scale memory fusion ... | HIT: 10.1016/j.patcog.2025.112581, alt-id S0031320325012440 (pii matches) |
| 2 | 2026-10-11 | api.crossref.org/works?query.title=MP-DRA multi-scale memory ... | HIT: 10.1016/j.neucom.2025.131427, alt-id S0925231225020995 (pii matches) |
| 3 | 2026-10-11 | api.crossref.org/journals/0031-3203/works?query.bibliographic=memory bank industrial anomaly detection MVTec / PatchCore coreset / unsupervised industrial AD localization, from 2024-01-01 | 45 rows; relevant ones selected (sec. 4) |
| 4 | 2026-10-11 | api.crossref.org/journals/0925-2312/works?... same 3 queries | 45 rows; relevant ones selected (sec. 4) |
| 5 | 2026-10-11 | doi.org content negotiation (Accept: application/x-bibtex) for 12 DOIs | all 12 returned BibTeX |
| 6 | 2026-10-11 | WebFetch scimagojr.com/journalsearch.php?q=0031-3203 and q=0925-2312 | 403 |
| 7 | 2026-10-11 | curl (browser UA) same Scimago URLs | 403 |
| 8 | 2026-10-11 | WebFetch scimagojr.com ...q=24807&tip=sid | 403 |
| 9 | 2026-10-11 | Built-in browser scimagojr.com ...q=24823&tip=sid | Cloudflare bot check; stopped (no CAPTCHA bypass) |
| 10 | 2026-10-11 | WebSearch "Pattern Recognition journal scimago SJR 2025 quartile..." | snippet: SJR 2025 = 2.147, Q1 Artificial Intelligence, Q1 Computer Vision and Pattern Recognition, H-index 267 (Scimago sid 24823) |
| 11 | 2026-10-11 | WebSearch "Neurocomputing scimago SJR 2025 quartile..." | snippet: SJR 2025 = 1.465, Q1 Artificial Intelligence, Q1 Computer Science Applications, H-index 233 (Scimago sid 24807) |
| 12 | 2026-10-11 | WebFetch sciencedirect.com/journal/pattern-recognition/about/insights | 403 |
| 13 | 2026-10-11 | WebFetch elsevier.com/journals/pattern-recognition/0031-3203/guide-for-authors | 301 -> sciencedirect (blocked) |
| 14 | 2026-10-11 | WebFetch sciencedirect.com/journal/pattern-recognition/publish/guide-for-authors | 403; built-in browser also blocked ("There was a problem providing the content") |
| 15 | 2026-10-11 | WebFetch ctan.org/pkg/elsarticle | v3.5, 2026-01-09, LPPL 1.3, maintainer C. V. Radhakrishnan |
| 16 | 2026-10-11 | curl ctan.org/tex-archive/macros/latex/contrib/elsarticle | files: elsarticle.cls, elsarticle-num.bst, elsarticle-harv.bst, elsarticle-num-names.bst, 3 templates, elsdoc |
| 17 | 2026-10-11 | WebFetch shop.elsevier.com/journals/pattern-recognition/0031-3203 | aims & scope; "single-column, double-spaced, 20-35 pages (40 for reviews)"; 12 issues/yr |
| 18 | 2026-10-11 | WebFetch shop.elsevier.com/journals/neurocomputing/0925-2312 | aims & scope (theory/practice/applications of neural nets & learning systems; applications incl. image processing, computer vision); Software Track |
| 19 | 2026-10-11 | WebFetch elsevier.com/researcher/author/policies-and-guidelines/latex-instructions | elsarticle is the recommended class; template ZIP; Overleaf (TeX Live 2022) ok; bib styles bundled |
| 20 | 2026-10-11 | curl elsevier.com/about/policies-and-standards/pricing -> legacyfileshare.elsevier.com/els_com_pricing/article-publishing-charge.xlsx | Official APC list "Prices as of date: 05-Oct-2026": Pattern Recognition Hybrid OA USD 3120 / EUR 2850 / GBP 2500; Neurocomputing Hybrid OA USD 2660 / EUR 2430 / GBP 2130 (excl. taxes) |
| 21 | 2026-10-11 | WebSearch PR guide for authors highlights/graphical abstract/review | snippet (from official GfA): 20-35 pp (40 review) single col double spaced; highlights 3-5 bullets <=85 chars, separate file; graphical abstract encouraged; single anonymized review |
| 22 | 2026-10-11 | WebSearch Neurocomputing guide for authors review/highlights/reference | snippet: single anonymized; highlights 3-5 bullets <=85 chars (encouraged); "Your Paper Your Way" - any consistent reference style at submission; 7 article types, Type 1 Regular article |
| 23 | 2026-10-11 | WebSearch PR guide: data availability / generative AI | snippet: GenAI-use declaration required at submission; data availability statement expected |
| 24 | 2026-10-11 | WebSearch PR insights review speed | snippet from sciencedirect insights: 18 d to first decision, 110 d to decision after review, 250 d to acceptance, 5 d acceptance->online; same snippet says IF 7.6, CiteScore 15.8, APC USD 2,800 -> STALE (APC contradicts row 20) |
| 25 | 2026-10-11 | WebSearch Neurocomputing insights review speed | snippet: 9 d to first decision, 77 d to decision after review, 192 d to acceptance (staleness unknown) |
| 26 | 2026-10-11 | en.wikipedia.org/wiki/Pattern_Recognition_(journal) | JIF 9.1 for 2025, cited to "2025 Journal Citation Reports", Clarivate (wording ambiguous: may be JCR release 2025 = JIF 2024) |
| 27 | 2026-10-11 | en.wikipedia.org/wiki/Neurocomputing_(journal) | JIF 5.5 for 2023, cited to 2023 JCR (Clarivate, 2024) - outdated |
| 28 | 2026-10-11 | WebSearch JCR 2026 PR/Neurocomputing JIF | only third-party aggregators (PR 9.1, Neuro 6.5) - not Clarivate |
| 29 | 2026-10-11 | WebSearch elsarticle-num / -harv | elsdoc: num = numerical, harv = author-year (natbib), num-names = numerical with names |

#### 2. Journal comparison

| Item | Pattern Recognition (0031-3203) | Neurocomputing (0925-2312) | Grade |
|---|---|---|---|
| Publisher / model | Elsevier, Hybrid OA (subscription route = no fee) | Elsevier, Hybrid OA (subscription route = no fee) | V-primary (APC xlsx, row 20) |
| OA APC | USD 3,120 excl. tax (as of 05-Oct-2026) | USD 2,660 excl. tax (as of 05-Oct-2026) | V-primary (row 20) |
| SJR (Scimago) | 2025: SJR 2.147; Q1 Artificial Intelligence; Q1 Computer Vision and Pattern Recognition; H 267 | 2025: SJR 1.465; Q1 Artificial Intelligence; Q1 Computer Science Applications; H 233 | V-snippet (Scimago blocked by 403/Cloudflare) |
| JCR (Clarivate) JIF | 9.1 per Wikipedia citing "2025 JCR" (likely JIF-2024). JCR quartile not verified | 5.5 (JIF 2023) per Wikipedia; newer value not verified | U for current; never equate SJR Q1 with JCR Q1 |
| Aims & scope fit | Theory, methodology and applications of pattern recognition; explicitly underpins computer vision / image processing. Industrial visual AD with methodological analysis (compression vs small-defect sensitivity) fits well; journal already publishes MMFNet, S3AD, memory-retrieval AD, feature-compression AD | Neural networks & learning systems: theory, practice, applications incl. image processing and computer vision. Fits; GfA says regular submissions must be directly relevant to neural networks and/or learning systems, so frame around learned feature representations | V-primary (shop.elsevier.com) |
| Article types | Original articles, reviews, pedagogical pieces, special issues | 7 types; Type 1 = Regular article; also Software Track | V-primary (PR); V-snippet (Neuro) |
| Length | 20-35 pages (40 for reviews), single column, double spaced, numbered pages | Not verified | V-primary (PR); U (Neuro) |
| Highlights | 3-5 bullets, <=85 chars each incl. spaces, separate editable file with "highlights" in name | 3-5 bullets <=85 chars (encouraged) | V-snippet |
| Graphical abstract | Encouraged | Not verified | V-snippet / U |
| Review model | Single anonymized | Single anonymized | V-snippet |
| Data availability statement | Expected (Data Availability section) | Listed in GfA ("data statement", "research data") - exact wording unverified | V-snippet |
| Declarations | Generative-AI use declaration at submission; competing-interest declaration (standard Elsevier) assumed but not read | GfA has a "generative AI" section; details unverified | V-snippet / U |
| LaTeX | elsarticle (Elsevier generic); no journal-specific template verified | elsarticle (Elsevier generic); no journal-specific template verified | V-primary (Elsevier LaTeX page) |
| Reference style | Not verified from GfA (published PR papers use numbered style -> elsarticle-num is the safe choice) | "Your Paper Your Way": any consistent style at submission; published style numbered -> elsarticle-num | U (PR) / V-snippet (Neuro) |
| Review speed | 18 d first decision; 110 d decision after review; 250 d to acceptance; 5 d acceptance->online | 9 d first decision; 77 d decision after review; 192 d to acceptance | V-snippet, possibly stale (same PR snippet carried old APC/IF) |

#### 3. elsarticle

- CTAN: https://ctan.org/pkg/elsarticle - version **3.5 (2026-01-09)**, licence **LPPL 1.3**, maintainer C. V. Radhakrishnan; in TeX Live and MiKTeX. (V-primary)
- Files (CTAN dir): elsarticle.cls; elsarticle-num.bst (numbered), elsarticle-harv.bst (author-year, natbib), elsarticle-num-names.bst (numbered with names); templates elsarticle-template-{num,harv,num-names}.tex; docs elsdoc.pdf. (V-primary)
- Elsevier LaTeX instructions: https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions - elsarticle is the recommended class, template ZIP from Elsevier, Overleaf OK (verify compile). (V-primary)
- Recommendation: `\documentclass[preprint,12pt]{elsarticle}` (or `review` option for double spacing to meet PR's "double spaced" rule), `\bibliographystyle{elsarticle-num}`, `\journal{Pattern Recognition}` / `\journal{Neurocomputing}`.

#### 4. BibTeX (all from doi.org content negotiation, 2026-10-11)

Fit anchors:

```bibtex
@article{Wang_2026, title={MMFNet: A multi-scale memory fusion network based on simulated abnormal samples for anomaly detection}, volume={172}, ISSN={0031-3203}, DOI={10.1016/j.patcog.2025.112581}, journal={Pattern Recognition}, publisher={Elsevier BV}, author={Wang, Pengxiang and Qin, Yuhua and Zong, Xulin and Wang, Chaoyue and Zhang, Hao}, year={2026}, month=apr, pages={112581} }

@article{Shao_2025, title={MP-DRA: Multi-scale memory and adaptive pseudo-anomaly enhanced open-set anomaly detection}, volume={655}, ISSN={0925-2312}, DOI={10.1016/j.neucom.2025.131427}, journal={Neurocomputing}, publisher={Elsevier BV}, author={Shao, Yunxue and Xu, Fangdi and Wang, Lingfeng}, year={2025}, month=nov, pages={131427} }
```

Pattern Recognition, related 2024-2026:

```bibtex
@article{Peng_2026, title={S3AD: Efficient industrial anomaly detection via selection, space, and scale}, volume={179}, ISSN={0031-3203}, DOI={10.1016/j.patcog.2026.113868}, journal={Pattern Recognition}, publisher={Elsevier BV}, author={Peng, Zhonghua and Dong, Chengyang and Liu, Bo and Li, Zuoyong and Zeng, Kun and Li, Jialong}, year={2026}, month=nov, pages={113868} }

@article{Hu_2026, title={Efficient industrial anomaly detection via cross-scale distillation with enhanced feature compression}, volume={173}, ISSN={0031-3203}, DOI={10.1016/j.patcog.2025.112761}, journal={Pattern Recognition}, publisher={Elsevier BV}, author={Hu, Ronglong and Yi, Jizheng and Li, Xiaoyao and Chen, Aibin and Han, Guangjie}, year={2026}, month=may, pages={112761} }

@article{Guo_2026, title={A memory and retrieval transformer-based unsupervised learning model for anomaly detection and segmentation}, volume={174}, ISSN={0031-3203}, DOI={10.1016/j.patcog.2025.113004}, journal={Pattern Recognition}, publisher={Elsevier BV}, author={Guo, Jiawei and Song, Ge and Wang, Yi}, year={2026}, month=jun, pages={113004} }

@article{Yang_2024, title={SLSG: Industrial image anomaly detection with improved feature embeddings and one-class classification}, volume={156}, ISSN={0031-3203}, DOI={10.1016/j.patcog.2024.110862}, journal={Pattern Recognition}, publisher={Elsevier BV}, author={Yang, Minghui and Liu, Jing and Yang, Zhiwei and Wu, Zhaoyang}, year={2024}, month=dec, pages={110862} }

@article{Zhou_2026, title={One-shot unsupervised industrial anomaly detection: Enhanced performance under extreme data scarcity}, volume={173}, ISSN={0031-3203}, DOI={10.1016/j.patcog.2025.112759}, journal={Pattern Recognition}, publisher={Elsevier BV}, author={Zhou, Jiayin and Wong, Waikeung and Liao, Fangjian}, year={2026}, month=may, pages={112759} }
```

Neurocomputing, related 2024-2026:

```bibtex
@article{Li_2027, title={BAMB: Unified industrial anomaly detection and classification via a mixed memory bank with boundary-aware coreset selection}, volume={708}, ISSN={0925-2312}, DOI={10.1016/j.neucom.2026.135250}, journal={Neurocomputing}, publisher={Elsevier BV}, author={Li, Yangyi and Jia, Ke and Chen, Qianzeng}, year={2027}, month=jan, pages={135250} }

@article{Luo_2024, title={DMMGNet: A discrimination mapping and memory bank mean guidance-based network for high-performance few-shot industrial anomaly detection}, volume={610}, ISSN={0925-2312}, DOI={10.1016/j.neucom.2024.128622}, journal={Neurocomputing}, publisher={Elsevier BV}, author={Luo, Aoshuang and Wen, Guojun and Cheng, Yahui and Mei, Shuang and Dong, Hongbo and Liu, Xingyue}, year={2024}, month=dec, pages={128622} }

@article{Zhang_2024, title={Learnable product quantization for anomaly detection}, volume={582}, ISSN={0925-2312}, DOI={10.1016/j.neucom.2024.127532}, journal={Neurocomputing}, publisher={Elsevier BV}, author={Zhang, Shi and Chen, Weilin and Lu, Binlong and Lai, Huixia}, year={2024}, month=may, pages={127532} }

@article{Hua_2026, title={Joint decision normalizing flow based on frequency separation for industrial anomaly detection and localization}, volume={668}, ISSN={0925-2312}, DOI={10.1016/j.neucom.2025.132206}, journal={Neurocomputing}, publisher={Elsevier BV}, author={Hua, Xingzhao and Chen, Yu and Hu, Yueming and Chen, Yili and Yan, Zhenting and Han, Jun and Huang, HuiLing}, year={2026}, month=mar, pages={132206} }

@article{Huang_2025, title={KD-KI: Knowledge distillation with knowledge infusion for anomaly detection and localization}, volume={656}, ISSN={0925-2312}, DOI={10.1016/j.neucom.2025.131423}, journal={Neurocomputing}, publisher={Elsevier BV}, author={Huang, Wei and Xu, Zhaonan and Wan, Rongchun and Yang, Xuhua and Zhang, Bingyang}, year={2025}, month=dec, pages={131423} }
```

Notes: Elsevier uses article numbers, not pages; the `pages` field holds the article number. BAMB (vol 708) is dated Jan 2027 in Crossref (online-first). Relevance judged from titles only (abstracts not read).

#### 5. Unverified / gaps

1. Scimago pages themselves (403 + Cloudflare); SJR 2025 values/quartiles come only from search snippets. Neurocomputing may also have a third Scimago category (e.g. Cognitive Neuroscience) not shown in snippet.
2. Current Clarivate JCR JIF and JCR quartile for both journals (only Wikipedia-cited 9.1 for PR and an outdated 5.5 JIF-2023 for Neurocomputing; aggregator "6.5" not trusted).
3. CiteScore (snippet said 15.8 for PR but from a stale snippet).
4. Review-speed figures: snippet-only, staleness unknown.
5. Neurocomputing length limit, graphical-abstract policy, exact data-statement and declaration wording.
6. Pattern Recognition required reference style (numbered assumed from published papers, not read in GfA); competing-interest declaration form.
7. Whether either journal currently requires double-anonymized submission for any track (snippets say single anonymized for both).
8. Full guide-for-authors text for both journals (ScienceDirect blocked to WebFetch, curl, and the built-in browser).

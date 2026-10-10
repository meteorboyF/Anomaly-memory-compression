# Data: provenance, licence, profile, known issues

## MVTec AD (original) — the only dataset in scope

| Field | Value (verified 2026-10-11 unless noted) |
|---|---|
| Name | MVTec Anomaly Detection (MVTec AD), original release (not AD 2, LOCO or 3D-AD) |
| Publisher pages | https://www.mvtec.com/research-teaching/datasets/mvtec-ad and `/downloads` |
| Licence | **CC BY-NC-SA 4.0**, re-read on the overview page 2026-10-11: non-commercial use only. Research use and publication of results are compatible. We never redistribute images or masks; GitHub holds scripts only |
| Citation requested | Bergmann et al., CVPR 2019 (doi:10.1109/CVPR.2019.00982) and IJCV 2021 (doi:10.1007/s11263-020-01400-4) |
| Access | The overview page shows a "Download dataset — Fill in the form" button. The public **downloads page lists direct links**, and the archive URL serves the file to an anonymous HTTP client with no login, token or waiting period (checked by HEAD + 16-byte range read: XZ magic `FD 37 7A 58 5A 00`). See "Access question" below |
| Archive | `mvtec_anomaly_detection.tar.xz`, **5,264,982,680 bytes** (Content-Length), ETag `"6127347e-139d14298"`, Last-Modified 2021-08-26, `Accept-Ranges: bytes` (resumable) |
| URL (recorded) | https://www.mydrive.ch/shares/150996/b52ecdcbf521176e9db9c731f2304b27/download/420938113-1629960298/mvtec_anomaly_detection.tar.xz. The tool re-resolves it from the downloads page on every acquisition |
| Publisher checksum | **None published** (downloads page checked). We record our own SHA-256, labelled `sha256_calculated_by_us`; it is never presented as a publisher checksum |
| Per-category archives | Also on the downloads page (104–705 MB each); not used, because the whole archive is one verified artifact |
| Published counts | IJCV 2021 Table 1: 3629 train-good / 467 test-good / 1258 test-defective (5354 images), 73 defect types, 1888 GT regions. Per-category counts are enforced by `configs/acquire_mvtec_ad.yaml` |
| Image properties | Square, 700–1024 px per side. grid, screw and zipper are single-channel |
| Ground truth | Pixel masks `ground_truth/<defect>/<stem>_mask.png`, test only. Annotation policy (IJCV §3): border/ambiguous pixels are preferably labelled anomalous; missing parts are annotated at the expected location |
| Official evaluation code | `mvtec_ad_evaluation.tar.xz` (11,056 B, SHA-256 by us `dfcda7d6…f220`), BSD-3, © 2022 MVTec. Metric functions vendored under `tests/reference/mvtec_official/` for verification only |

### Access question (for the researcher)

The project rules forbid access applications. What we observed:

- The overview page asks visitors to "fill in the form".
- The downloads page and the file itself are publicly reachable without it. A form that grants instant access is not an application, institutional-email requirement, DUA or waiting period.
- **You decide** whether to fill in MVTec's form yourself before Cell 2 runs. The tool needs nothing from it, and filling it in costs nothing.

If MVTec ever gates the link, the tool stops and prints the manual-upload instructions. Manual download and upload is allowed; manual annotation is not.

### Storage plan

| Item | Where | Size |
|---|---|---|
| Verified archive (compressed) | Drive `datasets/archives/` + `.verified.json` marker | 5.26 GB |
| Working copy (extracted) | Colab local disk `/content/amc_local/data/mvtec_ad` (re-staged per runtime) | ≈5–6 GB (estimate, to be measured) |
| Unpacked Drive copy | **Not made**: it would duplicate 5+ GB and FUSE reads are slower than re-extracting locally (DECISIONS D-003) | — |

### Profile

**Status: PENDING.** It needs Colab Cell 3 (`profile_data`, CPU), which has not been run. Nothing in this section is measured yet.

The profile will record:

- **Counts:** per-category counts checked against Table 1.
- **Images:** sizes and modes.
- **Defect areas:** native-resolution defect area fractions and connected components (8-connectivity).
- **Preprocessing losses:** what the PatchCore preprocessing loses (defects erased by Resize 256 → CenterCrop 224 plus the bilinear-and-floor mask rule, pixels and whole components outside the crop).
- **Duplicates:** exact file and pixel duplicates, including any that cross splits or categories (leakage).
- **Hashes:** the content hash `dataset_hash` and the `split_hash` that pin every later run.

### Known issues to check, from the literature

- Logical or "missing" anomalies (e.g. transistor `misplaced`, cable `missing_*`) are annotated where the part should be. This affects size strata, because the masks cover background-like pixels. They are reported, not removed.
- PatchCore's centre crop keeps the central 76.6 % of the image. EfficientAD's authors state that 99.9 % of MVTec AD defect pixels lie in that area. The profile measures this for our masks.
- MVTec publishes no errata. Do not "fix" masks: manual annotation is forbidden, and the official ground truth is the benchmark.

## Other datasets

**None are in scope.** Any additional dataset (e.g. VisA as a size-robustness check) must first pass these checks independently, recorded here before any download:

- access
- licence
- size
- included ground truth
- a published baseline

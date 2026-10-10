# Official MVTec AD evaluation code (test reference only)

Source: `mvtec_ad_evaluation.tar.xz`, linked as "Download the evaluation code"
from https://www.mvtec.com/research-teaching/datasets/mvtec-ad
(direct link https://www.mydrive.ch/shares/150450/bb24b914a28ddd2b5e35bd53d23177cd/download/439517473-1665675012/mvtec_ad_evaluation.tar.xz),
fetched 2026-10-11, archive SHA-256 (calculated by us)
`dfcda7d67eee25316ec6ae5042c0b1684a4cabf33b2346be351e2ce36013f220`,
Last-Modified 2022-10-13.

Licence: BSD-3-Clause, Copyright 2022 MVTec Software GmbH (`LICENSE.txt`,
reproduced unmodified as required by clause 1).

Used ONLY by `tests/test_metrics_reference.py` to check that
`anomaly_memory.eval.metrics` reproduces the official AU-PRO, PRO curve and
image-level AUROC exactly. Not imported by the package.

Modifications (permitted by the licence):
- `pro_curve_util.py`: the deprecated `scipy.ndimage.measurements.label`
  import is wrapped to prefer `scipy.ndimage.label` (same function).
- `generic_util.py`: excerpt containing only `trapezoid()`, unmodified, so
  the reference does not require `tifffile`.
- `roc_curve_util.py`: unmodified.

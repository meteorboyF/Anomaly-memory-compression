"""Image/mask geometry policies (resize + center crop), matching torchvision on PIL.

torchvision ``Resize(int)`` on a PIL image resizes the shorter side with
``PIL.Image.resize``; ``CenterCrop`` uses ``top = int(round((H - h) / 2))``.
Re-implemented here so CPU profiling does not need torch, and so mask
handling (nearest vs bilinear + threshold) is an explicit, recorded choice.
"""

from __future__ import annotations

import dataclasses
from typing import Literal

import numpy as np
from PIL import Image

_INTERP = {"nearest": Image.NEAREST, "bilinear": Image.BILINEAR, "bicubic": Image.BICUBIC}


@dataclasses.dataclass(frozen=True)
class GeometryPolicy:
    name: str
    resize: int | None  # shorter side; None = native
    crop: int | None  # square center crop; None = no crop
    image_interp: Literal["nearest", "bilinear", "bicubic"] = "bilinear"
    mask_interp: Literal["nearest", "bilinear"] = "nearest"
    mask_threshold: float = 0.5  # applied to [0,1] masks after bilinear resize

    def output_size(self, native_hw: tuple[int, int]) -> tuple[int, int]:
        h, w = resized_hw(native_hw, self.resize)
        if self.crop:
            return self.crop, self.crop
        return h, w


def resized_hw(hw: tuple[int, int], resize: int | None) -> tuple[int, int]:
    h, w = hw
    if resize is None:
        return h, w
    if h <= w:
        return resize, int(resize * w / h)
    return int(resize * h / w), resize


def crop_box(hw: tuple[int, int], crop: int) -> tuple[int, int, int, int]:
    """(top, left, bottom, right) in resized coordinates, torchvision rule."""
    h, w = hw
    if crop > h or crop > w:
        raise ValueError(f"crop {crop} larger than image {hw}")
    top = int(round((h - crop) / 2.0))
    left = int(round((w - crop) / 2.0))
    return top, left, top + crop, left + crop


def transform_mask(mask: np.ndarray, policy: GeometryPolicy) -> np.ndarray:
    """Native boolean mask -> boolean mask under the policy."""
    m = np.asarray(mask) > 0
    h, w = m.shape
    rh, rw = resized_hw((h, w), policy.resize)
    if (rh, rw) != (h, w):
        im = Image.fromarray((m * 255).astype(np.uint8), mode="L")
        im = im.resize((rw, rh), _INTERP[policy.mask_interp])
        arr = np.asarray(im, dtype=np.float32) / 255.0
        m = arr > policy.mask_threshold if policy.mask_interp != "nearest" else arr > 0.5
    if policy.crop:
        t, l, b, r = crop_box(m.shape, policy.crop)
        m = m[t:b, l:r]
    return m


def native_crop_window(native_hw: tuple[int, int], policy: GeometryPolicy) -> tuple[int, int, int, int]:
    """Approximate native-pixel window that survives the center crop."""
    h, w = native_hw
    if not policy.crop:
        return 0, 0, h, w
    rh, rw = resized_hw(native_hw, policy.resize)
    t, l, b, r = crop_box((rh, rw), policy.crop)
    sy, sx = h / rh, w / rw
    return int(round(t * sy)), int(round(l * sx)), int(round(b * sy)), int(round(r * sx))


def load_mask(path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("L")) > 0

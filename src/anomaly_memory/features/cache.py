"""Cache identity for frozen-backbone features.

A feature cache is reused only if every input that can change its bytes is
identical: dataset content hash, split hash, geometry policy, backbone
weights identity (name + weight-file SHA-256), layers, aggregation settings,
numeric precision, and the hash of the extraction code. Anything else is a
different cache.
"""

from __future__ import annotations

from ..io_utils import sha256_json

REQUIRED = ("dataset_hash", "split_hash", "geometry_policy", "backbone", "backbone_weights_sha256",
            "layers", "patch_aggregation", "precision", "code_hash")


def feature_cache_key(**parts) -> dict:
    missing = [k for k in REQUIRED if parts.get(k) in (None, "", [])]
    if missing:
        raise ValueError(f"feature cache key incomplete; missing {missing}")
    extra = sorted(set(parts) - set(REQUIRED))
    if extra:
        raise ValueError(f"unknown cache-key parts {extra}")
    return {"key": sha256_json(parts)[:20], "parts": parts}

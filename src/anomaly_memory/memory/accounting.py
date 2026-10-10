"""Actual memory cost of a normal-feature memory: banks, dtype, index overhead.

Compression ratios alone are not comparable across methods; every compared
configuration reports total bytes, including any search-index structures.
"""

from __future__ import annotations

import dataclasses

import numpy as np


@dataclasses.dataclass
class BankFootprint:
    name: str
    n_vectors: int
    dim: int
    dtype: str
    index_overhead_bytes: int = 0  # e.g. FAISS index structures, codebooks, ids

    @property
    def vector_bytes(self) -> int:
        return self.n_vectors * self.dim * np.dtype(self.dtype).itemsize

    @property
    def total_bytes(self) -> int:
        return self.vector_bytes + self.index_overhead_bytes


def total_memory(banks: list[BankFootprint]) -> dict:
    return {"banks": [dict(dataclasses.asdict(b), vector_bytes=b.vector_bytes, total_bytes=b.total_bytes)
                      for b in banks],
            "total_bytes": int(sum(b.total_bytes for b in banks))}


def vectors_for_budget(budget_bytes: int, dim: int, dtype: str, index_overhead_bytes: int = 0) -> int:
    """Largest bank size that fits ``budget_bytes`` (for matched-byte comparisons)."""
    per = dim * np.dtype(dtype).itemsize
    return max(0, (budget_bytes - index_overhead_bytes) // per)

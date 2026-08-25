from __future__ import annotations

import hashlib
import random
from typing import Any


def stable_seed(master_seed: int, *labels: Any) -> int:
    """Derive a stable 63-bit seed without Python's process-randomized hash()."""

    payload = "|".join([str(master_seed), *(str(label) for label in labels)]).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def random_stream(master_seed: int, *labels: Any) -> random.Random:
    return random.Random(stable_seed(master_seed, *labels))

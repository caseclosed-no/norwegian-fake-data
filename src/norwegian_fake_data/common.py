"""Shared input validation and bounded sampling."""

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")
MAX_COUNT = 100_000


def validate_count(count: int) -> None:
    if not 1 <= count <= MAX_COUNT:
        raise ValueError(f"count must be between 1 and {MAX_COUNT:,}.")


def sample_pool(pool: Sequence[T], count: int, unique: bool, rng: random.Random) -> list[T]:
    validate_count(count)
    if not pool:
        raise ValueError("No values match these options.")
    if unique:
        if count > len(pool):
            raise ValueError(
                f"Requested {count:,} unique values, but only {len(pool):,} are available."
            )
        return rng.sample(pool, count)
    return [rng.choice(pool) for _ in range(count)]

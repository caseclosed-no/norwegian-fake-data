"""Deliberately invalid US/UK identifiers for fictional records, generated offline."""

import random
from dataclasses import dataclass

from .common import sample_pool
from .data_sources import INTERNATIONAL_VERIFIED_ON, NINO_SOURCE, SSN_SOURCE


@dataclass(frozen=True)
class SsnRecord:
    ssn: str
    locale: str = "us"
    fictional_method: str = "invalid_000_prefix"
    invalid_reason: str = "SSA does not assign SSNs beginning with 000."
    source_url: str = SSN_SOURCE
    verified_on: str = INTERNATIONAL_VERIFIED_ON


@dataclass(frozen=True)
class NinoRecord:
    nino: str
    locale: str = "uk"
    fictional_method: str = "invalid_qq_prefix"
    invalid_reason: str = "HMRC excludes Q from both NINO prefix positions."
    source_url: str = NINO_SOURCE
    verified_on: str = INTERNATIONAL_VERIFIED_ON


def generate_ssns(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    compact: bool = False,
) -> list[SsnRecord]:
    """Sample 000-prefixed SSNs; compact output preserves all nine digits.

    SSA recommends 000-00-0000 or another combination beginning 000 for fictional
    displays. These identifiers do not encode a birthday, category, or state.
    """
    indices = sample_pool(range(1_000_000), count, unique, random.Random(seed))
    records = []
    for index in indices:
        digits = f"{index:06d}"
        value = f"000{digits}" if compact else f"000-{digits[:2]}-{digits[2:]}"
        records.append(SsnRecord(value))
    return records


def generate_ninos(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    compact: bool = False,
) -> list[NinoRecord]:
    """Sample invalid QQ-prefixed National Insurance numbers, with suffix A–D."""
    rng = random.Random(seed)
    # The suffix is not a separate identity: unique batches also keep the six
    # digits distinct, rather than reusing a number with another suffix.
    indices = sample_pool(range(1_000_000), count, unique, rng)
    records = []
    for index in indices:
        digits = f"{index:06d}"
        suffix = rng.choice("ABCD")
        value = (
            f"QQ{digits}{suffix}"
            if compact
            else f"QQ {digits[:2]} {digits[2:4]} {digits[4:]} {suffix}"
        )
        records.append(NinoRecord(value))
    return records

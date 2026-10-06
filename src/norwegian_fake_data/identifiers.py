"""Phone and car plate generators; no lookups or network access."""

import random
from typing import Literal

from .common import sample_pool
from .data_sources import PHONE_START, PHONE_STOP, PLATE_PREFIXES, PLATE_START, PLATE_STOP

PhoneStyle = Literal["spaced", "compact"]


def generate_phones(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    international: bool = False,
    style: PhoneStyle = "spaced",
) -> list[str]:
    """Sample Nkom's reserved TV/film numbers, optionally without replacement."""
    if style not in ("spaced", "compact"):
        raise ValueError("phone style must be spaced or compact.")
    numbers = sample_pool(range(PHONE_START, PHONE_STOP), count, unique, random.Random(seed))
    values = []
    for number in numbers:
        digits = str(number)
        value = " ".join(digits[i : i + 2] for i in range(0, 8, 2)) if style == "spaced" else digits
        if international:
            value = ("+47 " if style == "spaced" else "+47") + value
        values.append(value)
    return values


def generate_plates(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    prefix: str | None = None,
    compact: bool = False,
) -> list[str]:
    """Use only reviewed prefixes absent from the published Norwegian series."""
    if prefix is not None:
        prefix = prefix.upper()
        if prefix not in PLATE_PREFIXES:
            raise ValueError(f"prefix must be one of: {', '.join(PLATE_PREFIXES)}.")
    prefixes = (prefix,) if prefix else PLATE_PREFIXES
    span = PLATE_STOP - PLATE_START
    indices = sample_pool(range(len(prefixes) * span), count, unique, random.Random(seed))
    separator = "" if compact else " "
    return [f"{prefixes[i // span]}{separator}{PLATE_START + i % span}" for i in indices]

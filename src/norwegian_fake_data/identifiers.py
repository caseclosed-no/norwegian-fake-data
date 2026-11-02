"""Phone and car plate generators; no lookups or network access."""

import random
from typing import Literal

from .common import sample_pool
from .data_sources import PHONE_START, PHONE_STOP
from .plates import generate_plates as generate_plates  # Retain the existing import path.

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

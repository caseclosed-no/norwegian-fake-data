"""Offline, birth-year-weighted names from published SSB statistics."""

import gzip
import json
import random
from bisect import bisect_right
from dataclasses import dataclass
from datetime import date
from functools import cache, lru_cache
from importlib.resources import files
from itertools import accumulate
from typing import Literal

from .common import validate_count
from .fnr import age_on, birthday_pool

NameCategory = Literal["female", "male", "either"]
NameFallback = Literal["error", "nearest"]


@dataclass(frozen=True)
class NameRecord:
    name: str
    first_name: str
    last_name: str
    birthday: date
    age: int
    as_of: date
    category: str
    first_name_year: int
    surname_year: int
    first_name_approximate: bool
    surname_approximate: bool


@cache
def _snapshot() -> dict:
    resource = files("norwegian_fake_data").joinpath("data/names.json.gz")
    return json.loads(gzip.decompress(resource.read_bytes()))


def validate_name_options(category: str, fallback: str) -> None:
    if category not in ("female", "male", "either"):
        raise ValueError("category must be female, male, or either.")
    if fallback not in ("error", "nearest"):
        raise ValueError("name_fallback must be error or nearest.")


@cache
def _years(section: str) -> tuple[int, ...]:
    return tuple(sorted({int(key.split(":")[0]) for key in _snapshot()[section]}))


def _source_year(year: int, section: str, fallback: str) -> int:
    years = _years(section)
    if year in years:
        return year
    if fallback == "error":
        raise ValueError(
            f"SSB first-name data covers {years[0]}–{years[-1]}; "
            f"birth year {year} is outside this range. "
            'Use name_fallback="nearest" (CLI: --name-fallback nearest) to approximate.'
        )
    return min(years, key=lambda candidate: (abs(candidate - year), candidate))


def validate_name_years(birthdays: tuple[date, ...], fallback: NameFallback) -> None:
    """Reject unsupported years before sampling, independently of the seed."""
    for year in {birthday.year for birthday in birthdays}:
        _source_year(year, "first_names", fallback)


@lru_cache(maxsize=512)
def _distribution(section: str, key: str) -> tuple[tuple[str, ...], tuple[int, ...]]:
    rows = _snapshot()[section][key]
    names, weights = zip(*rows, strict=True)
    return names, tuple(accumulate(weights))


def _draw(section: str, key: str, rng: random.Random) -> str:
    names, cumulative = _distribution(section, key)
    return names[bisect_right(cumulative, rng.randrange(cumulative[-1]))]


def sample_name(
    birthday: date,
    as_of: date,
    *,
    category: NameCategory,
    name_fallback: NameFallback,
    rng: random.Random,
) -> NameRecord:
    """Sample a name for an already resolved birthday (also used by people)."""
    first_year = _source_year(birthday.year, "first_names", name_fallback)
    surname_year = _source_year(as_of.year, "surnames", "nearest")
    # An unspecified category is an even mixture, not weighted by name-list coverage.
    chosen_category = rng.choice(("female", "male")) if category == "either" else category
    first = _draw("first_names", f"{first_year}:{chosen_category}", rng)
    last = _draw("surnames", str(surname_year), rng)
    return NameRecord(
        name=f"{first} {last}",
        first_name=first,
        last_name=last,
        birthday=birthday,
        age=age_on(birthday, as_of),
        as_of=as_of,
        category=chosen_category,
        first_name_year=first_year,
        surname_year=surname_year,
        first_name_approximate=first_year != birthday.year,
        surname_approximate=surname_year != as_of.year,
    )


def generate_names(
    count: int = 1,
    *,
    birthday: date | None = None,
    age: int | None = None,
    exact_age: bool = False,
    as_of: date | None = None,
    category: NameCategory = "either",
    name_fallback: NameFallback = "error",
    seed: int | None = None,
) -> list[NameRecord]:
    """Generate names with replacement, using SSB weights for the actual birth year.

    Surnames use the nearest published story-year snapshot, independently of first
    names. `either` chooses the two SSB first-name categories with equal probability.
    """
    validate_count(count)
    validate_name_options(category, name_fallback)
    reference = as_of or date.today()
    days = birthday_pool(birthday=birthday, age=age, exact_age=exact_age, as_of=reference)
    validate_name_years(days, name_fallback)
    rng = random.Random(seed)
    return [
        sample_name(
            rng.choice(days), reference, category=category, name_fallback=name_fallback, rng=rng
        )
        for _ in range(count)
    ]

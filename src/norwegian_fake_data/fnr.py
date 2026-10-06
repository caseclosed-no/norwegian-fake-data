"""Fictional Norwegian FNRs for props and synthetic test data.

Generation uses the traditional allocation structure. Prop numbers deliberately
fail k2; synthetic numbers use a month outside the calendar range.
"""

import calendar
import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from .common import sample_pool, validate_count

FnrMode = Literal["prop", "synthetic"]
MIN_BIRTHDAY = date(1854, 1, 1)
MAX_BIRTHDAY = date(2039, 12, 31)
K1_WEIGHTS = (3, 7, 6, 1, 8, 9, 4, 5, 2)
K2_WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


@dataclass(frozen=True)
class FnrRecord:
    fnr: str
    birthday: date
    age: int
    mode: FnrMode
    as_of: date


def age_on(birthday: date, as_of: date) -> int:
    """Completed years; a Feb 29 birthday advances on Feb 28 in non-leap years."""
    anniversary = birthday.replace(
        year=as_of.year,
        day=min(birthday.day, calendar.monthrange(as_of.year, birthday.month)[1]),
    )
    return as_of.year - birthday.year - (as_of < anniversary)


def birthday_pool(
    *, birthday: date | None, age: int | None, exact_age: bool, as_of: date
) -> tuple[date, ...]:
    """All supported birthdays matching the request; uniform sampling is by day."""
    if (birthday is None) == (age is None):
        raise ValueError("Provide exactly one of --birthday YEAR MONTH DAY or --age N.")
    if exact_age and age is None:
        raise ValueError("--exact-age requires --age.")
    if birthday is not None:
        if not MIN_BIRTHDAY <= birthday <= MAX_BIRTHDAY:
            raise ValueError("Supported birth years are 1854 through 2039.")
        if birthday > as_of:
            raise ValueError("birthday cannot be after --as-of.")
        return (birthday,)
    if age is None or not 0 <= age <= 200:
        raise ValueError("age must be between 0 and 200.")
    if exact_age:
        year = as_of.year - age
        if not MIN_BIRTHDAY.year <= year <= MAX_BIRTHDAY.year:
            raise ValueError(
                "This age and reference date fall outside supported birth years (1854–2039)."
            )
        # Calendar subtraction: Feb 29 becomes Feb 28 in a non-leap birth year.
        chosen = date(year, as_of.month, min(as_of.day, calendar.monthrange(year, as_of.month)[1]))
        return (chosen,)
    # At most two calendar years: filtering makes leap-day and age-zero behavior
    # explicit, without approximating a year as 365 days.
    first_year = max(MIN_BIRTHDAY.year, as_of.year - age - 1)
    last_year = min(MAX_BIRTHDAY.year, as_of.year - age)
    if first_year > last_year:
        raise ValueError(
            "This age and reference date fall outside supported birth years (1854–2039)."
        )
    start = date(first_year, 1, 1)
    end = min(date(last_year, 12, 31), as_of)
    candidates = tuple(
        day
        for offset in range((end - start).days + 1)
        if (day := start + timedelta(days=offset)) <= as_of and age_on(day, as_of) == age
    )
    if not candidates:
        raise ValueError("No supported birthdays match this age and reference date.")
    return candidates


def individual_numbers(year: int) -> tuple[int, ...]:
    if 1854 <= year <= 1899:
        return tuple(range(500, 750))
    if 1900 <= year <= 1939:
        return tuple(range(500))
    if 1940 <= year <= 1999:
        return (*range(500), *range(900, 1000))
    if 2000 <= year <= 2039:
        return tuple(range(500, 1000))
    raise ValueError("Supported birth years are 1854 through 2039.")


def check_digits(first_nine: str) -> str | None:
    """Return traditional Mod-11 checksums, or None for an unusable candidate."""
    if len(first_nine) != 9 or not first_nine.isascii() or not first_nine.isdigit():
        raise ValueError("Expected exactly nine ASCII digits.")
    digits = [int(digit) for digit in first_nine]
    k1 = -sum(d * w for d, w in zip(digits, K1_WEIGHTS, strict=True)) % 11
    if k1 == 10:
        return None
    k2 = -sum(d * w for d, w in zip([*digits, k1], K2_WEIGHTS, strict=True)) % 11
    if k2 == 10:
        return None
    return f"{k1}{k2}"


def _number_pool(birthday: date, mode: FnrMode) -> list[str]:
    month = birthday.month + (80 if mode == "synthetic" else 0)
    prefix = f"{birthday.day:02d}{month:02d}{birthday.year % 100:02d}"
    values = []
    for individual in individual_numbers(birthday.year):
        first_nine = f"{prefix}{individual:03d}"
        checks = check_digits(first_nine)
        if checks is not None:
            if mode == "prop":
                checks = checks[0] + str((int(checks[1]) + 1) % 10)
            values.append(first_nine + checks)
    return values


def generate_fnrs(
    count: int = 1,
    *,
    birthday: date | None = None,
    age: int | None = None,
    exact_age: bool = False,
    as_of: date | None = None,
    mode: FnrMode = "prop",
    seed: int | None = None,
    unique: bool = False,
) -> list[FnrRecord]:
    """Generate fictional FNR records in prop or synthetic mode.

    Prop mode keeps k1 and shifts k2 by one modulo 10. Each usable traditional
    number therefore has exactly one deterministic prop counterpart.
    """
    validate_count(count)
    if mode not in ("prop", "synthetic"):
        raise ValueError("mode must be prop or synthetic.")
    reference = as_of or date.today()
    days = birthday_pool(birthday=birthday, age=age, exact_age=exact_age, as_of=reference)
    rng = random.Random(seed)
    pools: dict[date, list[str]] = {}
    if unique:
        pools = {day: _number_pool(day, mode) for day in days}
        capacity = sum(len(pool) for pool in pools.values())
        if count > capacity:
            raise ValueError(
                f"Requested {count:,} unique FNRs, but only {capacity:,} are available."
            )
    available_days = list(days)
    records = []
    for _ in range(count):
        day = rng.choice(available_days)
        if day not in pools:
            pools[day] = _number_pool(day, mode)
        pool = pools[day]
        # Sampling a day first preserves a uniform birthday distribution. For
        # unique batches, remove used candidates without unbounded retry loops.
        if unique:
            index = rng.randrange(len(pool))
            number = pool[index]
            pool[index] = pool[-1]
            pool.pop()
            if not pool:
                available_days.remove(day)
        else:
            number = sample_pool(pool, 1, False, rng)[0]
        records.append(FnrRecord(number, day, age_on(day, reference), mode, reference))
    return records

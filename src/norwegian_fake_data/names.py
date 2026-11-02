"""Offline birth-year-weighted names with optional socioeconomic background proxies."""

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

from . import name_profiles
from .common import validate_count
from .fnr import age_on, birthday_pool

NameCategory = Literal["female", "male", "either"]
NameFallback = Literal["error", "nearest", "historical"]
NameLocale = Literal["no", "us", "england"]
Background = Literal["any", "lower", "middle", "higher"]
BackgroundFallback = Literal["error", "unconditioned"]


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
    surname_year: int | None
    first_name_approximate: bool
    surname_approximate: bool
    name_locale: str = "no"
    background: str = "any"
    background_applied: str = "any"
    nssec: int | None = None
    sampling_method: str = "published_percentages"
    source_geography: str = "Norway"
    surname_geography: str = "Norway"
    surname_method: str = "published_counts"
    background_method: str = "none"
    background_period: str | None = None
    background_geography: str | None = None
    background_matched_mass: float | None = None
    background_cutoffs: str | None = None
    dataset_version: str = "ssb-2026-10-21"
    approximation_reasons: str = ""


@cache
def _snapshot() -> dict:
    resource = files("norwegian_fake_data").joinpath("data/names.json.gz")
    return json.loads(gzip.decompress(resource.read_bytes()))


def validate_name_options(
    category: str,
    fallback: str,
    name_locale: str = "no",
    background: str = "any",
    nssec: int | None = None,
    background_fallback: str = "error",
) -> None:
    if category not in ("female", "male", "either"):
        raise ValueError("category must be female, male, or either.")
    if fallback not in ("error", "nearest", "historical"):
        raise ValueError("name_fallback must be error, nearest, or historical.")
    if name_locale not in ("no", "us", "england"):
        raise ValueError("name_locale must be no, us, or england.")
    if background not in ("any", "lower", "middle", "higher"):
        raise ValueError("background must be any, lower, middle, or higher.")
    if background_fallback not in ("error", "unconditioned"):
        raise ValueError("background_fallback must be error or unconditioned.")
    if fallback == "historical" and name_locale != "england":
        raise ValueError("historical name_fallback is supported only for England names.")
    if nssec is not None:
        if name_locale != "england" or type(nssec) is not int or not 1 <= nssec <= 7:
            raise ValueError("nssec requires England names and an integer from 1 to 7.")
        if background != "any":
            raise ValueError("Choose either nssec or background, not both.")
    if name_locale == "no" and background != "any":
        raise ValueError("Norwegian names do not support socioeconomic backgrounds.")


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


def validate_name_years(
    birthdays: tuple[date, ...],
    fallback: NameFallback,
    name_locale: NameLocale = "no",
    category: NameCategory = "either",
    background: Background = "any",
    nssec: int | None = None,
    background_fallback: BackgroundFallback = "error",
) -> None:
    """Reject unsupported years before sampling, independently of the seed."""
    for year in {birthday.year for birthday in birthdays}:
        if name_locale == "no":
            _source_year(year, "first_names", fallback)
        else:
            for chosen in ("female", "male") if category == "either" else (category,):
                name_profiles.distribution(
                    name_locale, year, chosen, fallback, background, nssec, background_fallback
                )


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
    name_locale: NameLocale = "no",
    background: Background = "any",
    nssec: int | None = None,
    background_fallback: BackgroundFallback = "error",
) -> NameRecord:
    """Sample a name for an already resolved birthday (also used by people)."""
    if name_locale != "no":
        chosen = rng.choice(("female", "male")) if category == "either" else category
        first_names, first_weights, metadata = name_profiles.prepared_distribution(
            name_locale,
            birthday.year,
            chosen,
            name_fallback,
            background,
            nssec,
            background_fallback,
        )
        first = first_names[bisect_right(first_weights, rng.randrange(first_weights[-1]))]
        surnames, last_weights, surname_year = name_profiles.prepared_surnames(
            name_locale, as_of.year
        )
        last = surnames[bisect_right(last_weights, rng.randrange(last_weights[-1]))]
        metadata = dict(metadata)
        reasons = metadata["approximation_reasons"]
        if name_locale == "england":
            reasons = "; ".join(filter(None, (reasons, "curated British surname weights")))
        elif surname_year != as_of.year:
            reasons = "; ".join(
                filter(None, (reasons, "surname source year differs from story year"))
            )
        metadata["approximation_reasons"] = reasons
        return NameRecord(
            name=f"{first} {last}",
            first_name=first,
            last_name=last,
            birthday=birthday,
            age=age_on(birthday, as_of),
            as_of=as_of,
            category=chosen,
            surname_year=surname_year,
            surname_approximate=surname_year != as_of.year,
            name_locale=name_locale,
            background=background,
            nssec=nssec,
            surname_geography=name_profiles.snapshot(name_locale)["surname_geography"],
            surname_method="curated_weights" if name_locale == "england" else "published_counts",
            **metadata,
        )
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
        approximation_reasons="; ".join(
            reason
            for condition, reason in (
                (first_year != birthday.year, "first-name source year differs from birth year"),
                (surname_year != as_of.year, "surname source year differs from story year"),
            )
            if condition
        ),
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
    name_locale: NameLocale = "no",
    background: Background = "any",
    nssec: int | None = None,
    background_fallback: BackgroundFallback = "error",
) -> list[NameRecord]:
    """Generate names with replacement from the selected offline locale profile.

    Surnames use the nearest published story-year snapshot, independently of first
    names. `either` chooses the two source categories with equal probability.
    """
    validate_count(count)
    validate_name_options(
        category, name_fallback, name_locale, background, nssec, background_fallback
    )
    reference = as_of or date.today()
    days = birthday_pool(birthday=birthday, age=age, exact_age=exact_age, as_of=reference)
    validate_name_years(
        days, name_fallback, name_locale, category, background, nssec, background_fallback
    )
    rng = random.Random(seed)
    return [
        sample_name(
            rng.choice(days),
            reference,
            category=category,
            name_fallback=name_fallback,
            rng=rng,
            name_locale=name_locale,
            background=background,
            nssec=nssec,
            background_fallback=background_fallback,
        )
        for _ in range(count)
    ]

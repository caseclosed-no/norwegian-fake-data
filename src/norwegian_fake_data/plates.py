"""Reviewed fictional plate profiles. No valid or unchecked random-number mode."""

import random
from dataclasses import dataclass
from datetime import date
from typing import Literal

from .common import sample_pool, validate_count
from .data_sources import (
    CA_PLATE_SOURCE,
    CA_PLATE_STYLE_SOURCE,
    CA_PROP_LETTERS,
    GB_PLATE_DATE_SOURCE,
    GB_PLATE_SOURCE,
    INTERNATIONAL_VERIFIED_ON,
    PLATE_PREFIXES,
    PLATE_SOURCE,
    PLATE_START,
    PLATE_STOP,
    VERIFIED_ON,
)

Locale = Literal["no", "us", "uk"]
GB_SERIAL_LETTERS = "ABCDEFGHJKLMNOPRSTUVWXYZ"  # I and Q excluded; Z allowed here.
GB_FIRST_DATE = date(2001, 9, 1)
# September 2050 would require a three-digit identifier (100), outside this style.
GB_LAST_DATE = date(2050, 8, 31)


@dataclass(frozen=True)
class PlateRecord:
    plate: str
    locale: str
    state: str | None
    region: str | None
    vehicle_class: str
    plate_style: str
    registered_on: date | None
    as_of: date
    fictional_method: str
    invalid_reason: str
    source_url: str
    verified_on: str
    date_source_url: str | None = None


def _gb_age_code(registered_on: date) -> str:
    if not GB_FIRST_DATE <= registered_on <= GB_LAST_DATE:
        raise ValueError(
            "GB current-style registration dates must be 2001-09-01 through 2050-08-31."
        )
    year = registered_on.year % 100
    code = year if 3 <= registered_on.month <= 8 else year + 50
    if registered_on.month < 3:
        code -= 1
    return f"{code:02d}"


def _letters(index: int) -> str:
    alphabet = GB_SERIAL_LETTERS
    first, rest = divmod(index, len(alphabet) ** 2)
    second, third = divmod(rest, len(alphabet))
    return alphabet[first] + alphabet[second] + alphabet[third]


def generate_plate_records(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    prefix: str | None = None,
    compact: bool = False,
    locale: Locale = "no",
    state: str | None = None,
    region: str | None = None,
    registered_on: date | None = None,
    as_of: date | None = None,
) -> list[PlateRecord]:
    """Return plates with provenance; only passenger cars are supported.

    Norway retains its reviewed-prefix behavior. California uses the familiar
    1980-era layout with a DMV-deleted letter block. GB uses an impossible ZZ
    regional tag, a real age-code rule, and three permitted serial letters.
    """
    validate_count(count)
    if locale not in ("no", "us", "uk"):
        raise ValueError("locale must be no, us, or uk.")
    if state is not None and locale != "us":
        raise ValueError("--state is supported only with --locale us.")
    if region is not None and locale != "uk":
        raise ValueError("--region is supported only with --locale uk.")
    if prefix is not None and locale != "no":
        raise ValueError(
            "--prefix is supported only for Norwegian plates; fictional rules are fixed."
        )
    if registered_on is not None and locale != "uk":
        raise ValueError("--registered-on is supported only for GB plates.")
    reference = as_of or date.today()
    rng = random.Random(seed)
    separator = "" if compact else " "
    if locale == "no":
        if prefix is not None:
            prefix = prefix.upper()
            if prefix not in PLATE_PREFIXES:
                raise ValueError(f"prefix must be one of: {', '.join(PLATE_PREFIXES)}.")
        prefixes = (prefix,) if prefix else PLATE_PREFIXES
        span = PLATE_STOP - PLATE_START
        indices = sample_pool(range(len(prefixes) * span), count, unique, rng)
        values = [f"{prefixes[i // span]}{separator}{PLATE_START + i % span}" for i in indices]
        metadata = dict(
            state=None,
            region=None,
            plate_style="norwegian_reviewed_prefix",
            registered_on=None,
            fictional_method="reviewed_absent_prefix",
            invalid_reason="Prefix absent from published Norwegian series reviewed on 2026-10-06.",
            source_url=PLATE_SOURCE,
            verified_on=VERIFIED_ON,
        )
    elif locale == "us":
        if state is None:
            raise ValueError("US plates require --state CA; California is the verified profile.")
        state = state.upper()
        if state != "CA":
            raise ValueError(
                f"US state {state!r} is not supported. "
                "Only CA has a verified fictional plate profile."
            )
        if reference < date(1980, 1, 1):
            raise ValueError(
                "The California passenger plate profile requires --as-of in 1980 or later."
            )
        span = 9 * 1000
        indices = sample_pool(range(len(CA_PROP_LETTERS) * span), count, unique, rng)
        # Real CA seven-character layout; never allow caller-selected letter blocks.
        values = [
            f"{(i % span) // 1000 + 1}{CA_PROP_LETTERS[i // span]}{i % 1000:03d}" for i in indices
        ]
        metadata = dict(
            state=state,
            region=None,
            plate_style="california_legacy_passenger",
            registered_on=None,
            fictional_method="dmv_deleted_letter_block",
            invalid_reason=(
                "California DMV deletes SAM, FAN and GAT from regular and personalized plates."
            ),
            source_url=CA_PLATE_SOURCE,
            verified_on=INTERNATIONAL_VERIFIED_ON,
            date_source_url=CA_PLATE_STYLE_SOURCE,
        )
    else:
        region = "gb" if region is None else region.lower()
        if region != "gb":
            raise ValueError("Only --region gb is supported; Northern Ireland is not yet verified.")
        registration = registered_on or reference
        if registration > reference:
            raise ValueError("--registered-on cannot be after --as-of.")
        code = _gb_age_code(registration)
        indices = sample_pool(range(len(GB_SERIAL_LETTERS) ** 3), count, unique, rng)
        values = [f"ZZ{code}{separator}{_letters(i)}" for i in indices]
        metadata = dict(
            state=None,
            region=region,
            plate_style="gb_current_2001",
            registered_on=registration,
            fictional_method="invalid_zz_regional_tag",
            invalid_reason=(
                "DVLA excludes Z from the first two letters of current-style registrations."
            ),
            source_url=GB_PLATE_SOURCE,
            verified_on=INTERNATIONAL_VERIFIED_ON,
            date_source_url=GB_PLATE_DATE_SOURCE,
        )
    return [
        PlateRecord(
            plate=value, locale=locale, vehicle_class="passenger", as_of=reference, **metadata
        )
        for value in values
    ]


def generate_plates(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    prefix: str | None = None,
    compact: bool = False,
    locale: Locale = "no",
    state: str | None = None,
    region: str | None = None,
    registered_on: date | None = None,
    as_of: date | None = None,
) -> list[str]:
    """Generate plate strings; use generate_plate_records for provenance."""
    return [
        record.plate
        for record in generate_plate_records(
            count,
            seed=seed,
            unique=unique,
            prefix=prefix,
            compact=compact,
            locale=locale,
            state=state,
            region=region,
            registered_on=registered_on,
            as_of=as_of,
        )
    ]

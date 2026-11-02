"""Offline phone numbers from reviewed fictional-use ranges."""

import random
from dataclasses import dataclass
from typing import Literal

from .common import sample_pool
from .data_sources import PHONE_SOURCE, PHONE_START, PHONE_STOP, VERIFIED_ON

PhoneStyle = Literal["spaced", "compact"]
PhoneLocale = Literal["no", "us", "uk"]
PhoneKind = Literal["mobile", "landline"]
US_SOURCE = "https://nanpa.com/numbering/555-line-numbers"
UK_SOURCE = "https://www.ofcom.org.uk/phones-and-broadband/phone-numbers/numbers-for-drama"
PHONE_VERIFIED_ON = "2026-11-02"
# Reviewed selection, not an exhaustive US area-code directory.
# NYC: NANPA 2015 annual report; California: CPUC's current area-code table.
US_AREA_CODE_SOURCES = (
    "https://www.nationalnanpa.com/reports/2015_NANPA_Annual_Report.pdf",
    "https://www.cpuc.ca.gov/AreaCodes/",
)
US_AREA_CODES = ("212", "213", "310", "323", "408", "415", "424", "628", "646", "650", "669", "917")
# Prefix and grouping lengths for each of Ofcom's geographic drama ranges.
UK_LANDLINES = {
    "leeds": ("01134960", (4, 3, 4)),
    "sheffield": ("01144960", (4, 3, 4)),
    "nottingham": ("01154960", (4, 3, 4)),
    "leicester": ("01164960", (4, 3, 4)),
    "bristol": ("01174960", (4, 3, 4)),
    "reading": ("01184960", (4, 3, 4)),
    "birmingham": ("01214960", (4, 3, 4)),
    "edinburgh": ("01314960", (4, 3, 4)),
    "glasgow": ("01414960", (4, 3, 4)),
    "liverpool": ("01514960", (4, 3, 4)),
    "manchester": ("01614960", (4, 3, 4)),
    "london": ("02079460", (3, 4, 4)),
    "tyneside": ("01914980", (4, 3, 4)),
    "northern-ireland": ("02896496", (3, 4, 4)),
    "cardiff": ("02920180", (3, 4, 4)),
    "generic": ("01632960", (5, 6)),
}


@dataclass(frozen=True)
class PhoneRecord:
    phone: str
    locale: str
    profile: str
    area_code: str | None
    city: str | None
    fictional_method: str
    source_url: str
    verified_on: str
    area_code_source_url: str | None = None


def generate_phone_records(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    international: bool = False,
    style: PhoneStyle = "spaced",
    locale: PhoneLocale = "no",
    area_code: str | None = None,
    kind: PhoneKind | None = None,
    city: str | None = None,
) -> list[PhoneRecord]:
    """Sample a single reserved profile; reject irrelevant selection options."""
    if style not in ("spaced", "compact"):
        raise ValueError("phone style must be spaced or compact.")
    if locale not in ("no", "us", "uk"):
        raise ValueError("phone locale must be no, us, or uk.")
    if locale != "us" and area_code is not None:
        raise ValueError("area-code is only supported for US phones.")
    if locale != "uk" and (kind is not None or city is not None):
        raise ValueError("kind and city are only supported for UK phones.")
    area_source = None
    if locale == "no":
        pool, groups, country = range(PHONE_START, PHONE_STOP), (2, 2, 2, 2), "+47"
        prefix, profile, source, verified = "", "tv-film", PHONE_SOURCE, VERIFIED_ON
    elif locale == "us":
        area_code = "212" if area_code is None else area_code
        if area_code not in US_AREA_CODES:
            raise ValueError("Reviewed US area codes: " + ", ".join(US_AREA_CODES) + ".")
        pool, groups, country = range(100, 200), (3, 3, 4), "+1"
        prefix, profile, source, verified = (
            area_code + "5550",
            "555-01xx",
            US_SOURCE,
            PHONE_VERIFIED_ON,
        )
        area_source = US_AREA_CODE_SOURCES[0 if area_code in ("212", "646", "917") else 1]
    else:
        kind = "mobile" if kind is None else kind
        if kind not in ("mobile", "landline"):
            raise ValueError("UK phone kind must be mobile or landline.")
        if kind == "mobile":
            if city is not None:
                raise ValueError("city requires UK kind landline.")
            prefix, groups = "07700900", (5, 6)
        else:
            city = "generic" if city is None else city.lower().replace(" ", "-")
            if city not in UK_LANDLINES:
                raise ValueError("Reviewed UK cities: " + ", ".join(UK_LANDLINES) + ".")
            prefix, groups = UK_LANDLINES[city]
        pool, country = range(1000), "+44"
        profile, source, verified = kind, UK_SOURCE, PHONE_VERIFIED_ON
    values = sample_pool(pool, count, unique, random.Random(seed))
    records = []
    for number in values:
        digits = str(number) if locale == "no" else prefix + f"{number:03d}"
        parts, start = [], 0
        for size in groups:
            parts.append(digits[start : start + size])
            start += size
        if international:
            if locale == "uk":
                parts[0] = parts[0][1:]
            parts.insert(0, country)
        value = (" " if style == "spaced" else "").join(parts)
        records.append(
            PhoneRecord(
                value,
                locale,
                profile,
                area_code,
                city,
                "reserved_fictional_range",
                source,
                verified,
                area_source,
            )
        )
    return records


def generate_phones(
    count: int = 1,
    *,
    seed: int | None = None,
    unique: bool = False,
    international: bool = False,
    style: PhoneStyle = "spaced",
    locale: PhoneLocale = "no",
    area_code: str | None = None,
    kind: PhoneKind | None = None,
    city: str | None = None,
) -> list[str]:
    """Return formatted phone strings; Norway remains the default."""
    return [
        record.phone
        for record in generate_phone_records(
            count,
            seed=seed,
            unique=unique,
            international=international,
            style=style,
            locale=locale,
            area_code=area_code,
            kind=kind,
            city=city,
        )
    ]

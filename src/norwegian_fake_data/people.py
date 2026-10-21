"""Small character records built from the same identifier generators."""

import random
import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from .common import validate_count
from .data_sources import PHONE_START, PHONE_STOP
from .fnr import FnrMode, birthday_pool, generate_fnrs
from .identifiers import generate_phones, generate_plates
from .names import (
    NameCategory,
    NameFallback,
    sample_name,
    validate_name_options,
    validate_name_years,
)


@dataclass(frozen=True)
class PersonRecord:
    name: str
    birthday: date
    age: int
    fnr: str
    mode: FnrMode
    as_of: date
    phone: str
    email: str
    plate: str | None
    category: str
    first_name_year: int
    surname_year: int
    first_name_approximate: bool
    surname_approximate: bool


def generate_people(
    count: int = 1,
    *,
    birthday: date | None = None,
    age: int | None = None,
    exact_age: bool = False,
    as_of: date | None = None,
    mode: FnrMode = "prop",
    seed: int | None = None,
    unique: bool = False,
    vehicle: bool = False,
    category: NameCategory = "either",
    name_fallback: NameFallback = "error",
) -> list[PersonRecord]:
    """Compose exportable records; unique applies to FNR, phone, email and plate.

    A birthday or age is required, as for generate_fnrs. Names are fictional
    combinations and may repeat or coincide with real names.
    """
    validate_count(count)
    validate_name_options(category, name_fallback)
    if unique and count > PHONE_STOP - PHONE_START:
        raise ValueError("Only 10,000 unique phone numbers are available for character records.")
    reference = as_of or date.today()
    days = birthday_pool(birthday=birthday, age=age, exact_age=exact_age, as_of=reference)
    validate_name_years(days, name_fallback)
    rng = random.Random(seed)
    # Child seeds keep the individual generator APIs independent of one another.
    fnrs = generate_fnrs(
        count,
        birthday=birthday,
        age=age,
        exact_age=exact_age,
        as_of=reference,
        mode=mode,
        seed=rng.getrandbits(64),
        unique=unique,
        sex=None if category == "either" else category,
    )
    phones = generate_phones(count, seed=rng.getrandbits(64), unique=unique)
    plates = (
        generate_plates(count, seed=rng.getrandbits(64), unique=unique)
        if vehicle
        else [None] * count
    )
    people = []
    for index, (fnr, phone, plate) in enumerate(zip(fnrs, phones, plates, strict=True), start=1):
        # Traditional FNR allocation encodes sex in the ninth digit.
        name = sample_name(
            fnr.birthday,
            fnr.as_of,
            category="male" if int(fnr.fnr[8]) % 2 else "female",
            name_fallback=name_fallback,
            rng=rng,
        )
        email_name = f"{name.first_name}.{name.last_name}".lower().translate(
            str.maketrans({"æ": "ae", "ø": "o", "å": "a"})
        )
        email_name = unicodedata.normalize("NFKD", email_name).encode("ascii", "ignore").decode()
        email_name = re.sub(r"[^a-z0-9.-]+", "", email_name)
        people.append(
            PersonRecord(
                name.name,
                fnr.birthday,
                fnr.age,
                fnr.fnr,
                fnr.mode,
                fnr.as_of,
                phone,
                f"{email_name}.{index}@example.com",
                plate,
                name.category,
                name.first_name_year,
                name.surname_year,
                name.first_name_approximate,
                name.surname_approximate,
            )
        )
    return people

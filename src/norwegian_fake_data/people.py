"""Small character records built from the same identifier generators."""

import random
from dataclasses import dataclass
from datetime import date

from .common import validate_count
from .data_sources import PHONE_START, PHONE_STOP
from .fnr import FnrMode, generate_fnrs
from .identifiers import generate_phones, generate_plates

# Hand-curated combinations, not records of real people or population statistics.
FIRST_NAMES = (
    "Astrid",
    "Bjørn",
    "Eirik",
    "Ingrid",
    "Kari",
    "Lars",
    "Liv",
    "Magnus",
    "Sigrid",
    "Åse",
)
LAST_NAMES = (
    "Bakke",
    "Berg",
    "Dahl",
    "Hagen",
    "Haugen",
    "Lunde",
    "Moen",
    "Solberg",
    "Strand",
    "Vik",
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
) -> list[PersonRecord]:
    """Compose exportable records; unique applies to FNR, phone, email and plate.

    A birthday or age is required, as for generate_fnrs. Names are fictional
    combinations and may repeat or coincide with real names.
    """
    validate_count(count)
    if unique and count > PHONE_STOP - PHONE_START:
        raise ValueError("Only 10,000 unique phone numbers are available for character records.")
    rng = random.Random(seed)
    # Child seeds keep the individual generator APIs independent of one another.
    fnrs = generate_fnrs(
        count,
        birthday=birthday,
        age=age,
        exact_age=exact_age,
        as_of=as_of,
        mode=mode,
        seed=rng.getrandbits(64),
        unique=unique,
    )
    phones = generate_phones(count, seed=rng.getrandbits(64), unique=unique)
    plates = (
        generate_plates(count, seed=rng.getrandbits(64), unique=unique)
        if vehicle
        else [None] * count
    )
    people = []
    for index, (fnr, phone, plate) in enumerate(zip(fnrs, phones, plates, strict=True), start=1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        email_name = f"{first}.{last}".lower().translate(
            str.maketrans({"æ": "ae", "ø": "o", "å": "a"})
        )
        people.append(
            PersonRecord(
                f"{first} {last}",
                fnr.birthday,
                fnr.age,
                fnr.fnr,
                fnr.mode,
                fnr.as_of,
                phone,
                f"{email_name}.{index}@example.com",
                plate,
            )
        )
    return people

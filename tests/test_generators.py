import random
from dataclasses import asdict
from datetime import date, timedelta

import pytest

from norwegian_fake_data import generate_fnrs, generate_people, generate_phones, generate_plates
from norwegian_fake_data.fnr import age_on, birthday_pool, check_digits, individual_numbers

REFERENCE = date(2026, 10, 6)


def checksum_remainders(number):
    """Independent checksum validation, including the two check digits themselves."""
    digits = [int(digit) for digit in number]
    first = (
        sum(d * w for d, w in zip(digits[:10], (3, 7, 6, 1, 8, 9, 4, 5, 2, 1), strict=True)) % 11
    )
    second = sum(d * w for d, w in zip(digits, (5, 4, 3, 2, 7, 6, 5, 4, 3, 2, 1), strict=True)) % 11
    return first, second


def test_phone_entire_unique_pool():
    numbers = generate_phones(10_000, seed=12, unique=True, style="compact")
    assert set(numbers) == {str(value) for value in range(68050000, 68060000)}
    with pytest.raises(ValueError, match="10,000"):
        generate_phones(10_001, unique=True)


def test_phone_formats_preserve_number():
    plain = generate_phones(seed=7, style="compact")[0]
    assert generate_phones(seed=7)[0].replace(" ", "") == plain
    assert generate_phones(seed=7, international=True)[0].replace(" ", "") == "+47" + plain
    assert generate_phones(seed=7, international=True, style="compact") == ["+47" + plain]


def test_plates_full_single_prefix_pool():
    plates = generate_plates(90_000, unique=True, prefix="qb", seed=73)
    assert len(set(plates)) == 90_000
    assert "QB 10000" in plates
    assert "QB 99999" in plates
    assert all(plate.startswith("QB ") for plate in plates)
    with pytest.raises(ValueError, match="90,000"):
        generate_plates(90_001, unique=True, prefix="QB")


@pytest.mark.parametrize("prefix", ["EL", "CD", "AA", "XX", "XY", "XZ", "QZ", ""])
def test_assigned_or_unreviewed_prefix_rejected(prefix):
    with pytest.raises(ValueError, match="prefix"):
        generate_plates(prefix=prefix)


def test_plate_allowlist_and_compact_format():
    spaced = generate_plates(100, seed=1)
    assert {value[:2] for value in spaced} == {"QA", "QB", "QC"}
    assert generate_plates(100, seed=1, compact=True) == [p.replace(" ", "") for p in spaced]


@pytest.mark.parametrize("mode", ["prop", "synthetic"])
@pytest.mark.parametrize(
    "birthday",
    [
        date(1854, 1, 1),
        date(1899, 12, 31),
        date(1900, 1, 1),
        date(1939, 12, 31),
        date(1940, 1, 1),
        date(1999, 12, 31),
        date(2000, 2, 29),
        date(2039, 12, 31),
    ],
)
def test_fnr_structure_and_modes(mode, birthday):
    records = generate_fnrs(100, birthday=birthday, mode=mode, as_of=date(2040, 1, 1), seed=4)
    for record in records:
        number = record.fnr
        assert len(number) == 11 and number.isascii() and number.isdigit()
        assert int(number[:2]) == birthday.day
        assert int(number[2:4]) == birthday.month + (80 if mode == "synthetic" else 0)
        assert int(number[4:6]) == birthday.year % 100
        individual = int(number[6:9])
        if birthday.year < 1900:
            assert 500 <= individual <= 749
        elif birthday.year < 1940:
            assert 0 <= individual <= 499
        elif birthday.year < 2000:
            assert individual <= 499 or individual >= 900
        else:
            assert 500 <= individual <= 999
        first, second = checksum_remainders(number)
        assert first == 0
        if mode == "prop":
            # 2032 accepts additional k1 remainders, but still requires k2 == 0.
            assert second != 0
        else:
            assert second == 0
        assert record.birthday == birthday and record.mode == mode


def test_documented_checksum_vectors():
    # Skatteetaten's published 2032 documentation includes these traditional examples.
    assert check_digits("020132999") == "97"
    assert check_digits("301082999") == "20"
    # Exhaust each nine-digit suffix to exercise rejected k1 and k2 values.
    candidates = [check_digits(f"170587{value:03d}") for value in range(1000)]
    assert None in candidates
    for suffix, checks in enumerate(candidates):
        if checks is not None:
            assert checksum_remainders(f"170587{suffix:03d}{checks}") == (0, 0)


@pytest.mark.parametrize("generator", [generate_fnrs, generate_people])
def test_valid_mode_is_rejected_by_python_api(generator):
    with pytest.raises(ValueError, match="mode must be prop or synthetic"):
        generator(age=35, as_of=REFERENCE, mode="valid")


def test_random_birthday_pool_has_exact_age_boundaries():
    days = birthday_pool(birthday=None, age=35, exact_age=False, as_of=REFERENCE)
    assert days[0] == date(1990, 10, 7)
    assert days[-1] == date(1991, 10, 6)
    assert len(days) == 365
    for day in days:
        assert age_on(day, REFERENCE) == 35
    records = generate_fnrs(300, age=35, as_of=REFERENCE, seed=7)
    assert len({r.birthday for r in records}) > 100
    assert all(r.birthday in days and r.age == 35 for r in records)


def test_exact_age_and_leap_day_convention():
    assert generate_fnrs(age=35, exact_age=True, as_of=REFERENCE)[0].birthday == date(1991, 10, 6)
    leap = date(2000, 2, 29)
    assert age_on(leap, date(2023, 2, 27)) == 22
    assert age_on(leap, date(2023, 2, 28)) == 23
    assert age_on(leap, date(2024, 2, 28)) == 23
    assert age_on(leap, date(2024, 2, 29)) == 24
    assert generate_fnrs(age=1, exact_age=True, as_of=date(2024, 2, 29))[0].birthday == date(
        2023, 2, 28
    )
    pool = birthday_pool(birthday=None, age=23, exact_age=False, as_of=date(2023, 2, 28))
    assert leap in pool
    assert date(2000, 2, 28) in pool
    assert date(1999, 2, 28) not in pool


def test_age_zero_and_supported_year_boundaries():
    records = generate_fnrs(50, age=0, as_of=REFERENCE, seed=5)
    assert all(date(2025, 10, 7) <= r.birthday <= REFERENCE and r.age == 0 for r in records)
    days = birthday_pool(birthday=None, age=0, exact_age=False, as_of=date(1854, 1, 1))
    assert days == (date(1854, 1, 1),)


@pytest.mark.parametrize("mode", ["prop", "synthetic"])
def test_fnr_finite_unique_pool(mode):
    birthday = date(1987, 5, 17)
    month = 85 if mode == "synthetic" else 5
    usable = sum(
        check_digits(f"17{month:02d}87{individual:03d}") is not None
        for individual in individual_numbers(1987)
    )
    records = generate_fnrs(usable, birthday=birthday, mode=mode, unique=True, seed=3)
    assert len({r.fnr for r in records}) == usable
    with pytest.raises(ValueError, match="available"):
        generate_fnrs(usable + 1, birthday=birthday, mode=mode, unique=True)


def test_age_based_unique_batch():
    records = generate_fnrs(1000, age=35, as_of=REFERENCE, unique=True, seed=8)
    assert len({r.fnr for r in records}) == 1000
    assert all(r.age == 35 for r in records)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"birthday": date(1987, 5, 17), "age": 35},
        {"age": -1},
        {"age": 201},
        {"birthday": date(1853, 12, 31)},
        {"birthday": date(2040, 1, 1)},
        {"birthday": REFERENCE + timedelta(days=1)},
        {"age": 200},
        {"birthday": date(1987, 5, 17), "exact_age": True},
        {"age": 30, "mode": "bogus"},
    ],
)
def test_invalid_fnr_requests(kwargs):
    with pytest.raises(ValueError):
        generate_fnrs(as_of=REFERENCE, **kwargs)


@pytest.mark.parametrize(
    "generator,kwargs",
    [
        (generate_phones, {}),
        (generate_plates, {}),
        (generate_fnrs, {"age": 35, "as_of": REFERENCE}),
        (generate_people, {"age": 35, "as_of": REFERENCE, "vehicle": True}),
    ],
)
def test_seed_and_global_rng_isolation(generator, kwargs):
    state = random.getstate()
    assert generator(10, seed=42, **kwargs) == generator(10, seed=42, **kwargs)
    assert generator(10, seed=42, **kwargs) != generator(10, seed=43, **kwargs)
    assert random.getstate() == state
    for count in (0, -1, 100_001):
        with pytest.raises(ValueError, match="count"):
            generator(count, **kwargs)


def test_people_consistent_records_and_unique_identifiers():
    people = generate_people(100, age=42, as_of=REFERENCE, seed=73, unique=True, vehicle=True)
    for field in ("fnr", "phone", "email", "plate"):
        assert len({getattr(person, field) for person in people}) == 100
    for person in people:
        assert person.fnr[:6] == person.birthday.strftime("%d%m%y")
        assert person.age == age_on(person.birthday, REFERENCE) == 42
        assert checksum_remainders(person.fnr)[1] != 0
        assert person.email.endswith("@example.com") and person.email.isascii()
        assert person.plate[:2] in {"QA", "QB", "QC"}
        assert asdict(person)["as_of"] == REFERENCE
    assert generate_people(age=42)[0].plate is None


def test_synthetic_people_have_non_calendar_months():
    people = generate_people(50, age=35, as_of=REFERENCE, mode="synthetic", seed=73)
    for person in people:
        assert int(person.fnr[2:4]) == person.birthday.month + 80
        assert checksum_remainders(person.fnr) == (0, 0)

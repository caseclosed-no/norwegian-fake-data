import random
from collections import Counter
from datetime import date

import pytest

from norwegian_fake_data import generate_fnrs, generate_names, generate_people, names

REFERENCE = date(2026, 10, 21)


def test_real_snapshot_coverage_and_integrity():
    snapshot = names._snapshot()
    assert snapshot["schema_version"] == 1
    assert snapshot["license"] == "CC BY 4.0"
    assert set(snapshot["sources"]) == {"10467", "12891"}
    assert names._years("first_names") == tuple(range(1880, 2026))
    assert names._years("surnames") == tuple(range(2018, 2026))
    for year in range(1880, 2026):
        for category in ("female", "male"):
            rows = snapshot["first_names"][f"{year}:{category}"]
            assert rows
            assert all(isinstance(w, int) and w > 0 and n for n, w in rows)
    for rows in snapshot["surnames"].values():
        assert all(isinstance(w, int) and w >= 200 and n for n, w in rows)
    # Published 2025 percentages: preserve precision instead of using rankings.
    female = dict(snapshot["first_names"]["2025:female"])
    assert female["Emma"] > female["Iben"]


def test_sampling_uses_proportional_weights_and_exact_boundaries(monkeypatch):
    monkeypatch.setattr(names, "_distribution", lambda *args: (("Rare", "Common"), (1, 4)))

    class Ticket:
        def __init__(self, value):
            self.value = value

        def randrange(self, stop):
            assert stop == 4
            return self.value

    assert [names._draw("first_names", "test", Ticket(i)) for i in range(4)] == [
        "Rare",
        "Common",
        "Common",
        "Common",
    ]
    rng = random.Random(73)
    counts = Counter(names._draw("first_names", "test", rng) for _ in range(10_000))
    assert 0.72 < counts["Common"] / 10_000 < 0.78


def test_age_resolves_actual_birth_year_and_repeatable_records():
    state = random.getstate()
    kwargs = dict(age=70, as_of=REFERENCE, seed=73)
    records = generate_names(200, **kwargs)
    assert records == generate_names(200, **kwargs)
    assert records != generate_names(200, **{**kwargs, "seed": 74})
    assert random.getstate() == state
    assert {r.first_name_year for r in records} == {1955, 1956}
    assert {r.category for r in records} == {"female", "male"}
    for r in records:
        assert r.age == 70
        assert r.first_name_year == r.birthday.year
        assert not r.first_name_approximate
        assert r.surname_year == 2025 and r.surname_approximate
        assert r.first_name in dict(
            names._snapshot()["first_names"][f"{r.birthday.year}:{r.category}"]
        )
        assert r.name == f"{r.first_name} {r.last_name}"


@pytest.mark.parametrize("category", ["female", "male"])
@pytest.mark.parametrize("mode", ["prop", "synthetic"])
def test_people_name_category_and_fnr_are_consistent(category, mode):
    records = generate_people(
        100, age=42, as_of=REFERENCE, category=category, mode=mode, unique=True, seed=73
    )
    assert {r.category for r in records} == {category}
    for r in records:
        assert int(r.fnr[8]) % 2 == (category == "male")
        assert r.first_name_year == r.birthday.year
        assert r.email.isascii() and r.email.endswith("@example.com")
    assert len({r.fnr for r in records}) == len(records)
    mixed = generate_people(100, age=42, as_of=REFERENCE, mode=mode, seed=73)
    assert {r.category for r in mixed} == {"female", "male"}
    assert all((int(r.fnr[8]) % 2 == 1) == (r.category == "male") for r in mixed)


@pytest.mark.parametrize("year,expected", [(1854, 1880), (2039, 2025)])
@pytest.mark.parametrize("generator", [generate_names, generate_people])
def test_outside_coverage_requires_explicit_fallback(year, expected, generator):
    kwargs = dict(birthday=date(year, 1, 1), as_of=date(2040, 1, 1))
    with pytest.raises(ValueError, match="SSB first-name data covers"):
        generator(**kwargs)
    record = generator(**kwargs, name_fallback="nearest")[0]
    assert record.first_name_year == expected and record.first_name_approximate
    assert record.birthday.year == year


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("generator", [generate_names, generate_people])
def test_partially_unsupported_age_pool_fails_independently_of_seed(generator, seed):
    with pytest.raises(ValueError, match="birth year 2026"):
        generator(age=0, as_of=REFERENCE, seed=seed)


@pytest.mark.parametrize(
    "story_year,source_year", [(1900, 2018), (2018, 2018), (2022, 2022), (2030, 2025)]
)
def test_surname_snapshot_uses_story_year(story_year, source_year):
    record = generate_names(birthday=date(1880, 1, 1), as_of=date(story_year, 1, 1))[0]
    assert record.surname_year == source_year
    assert record.surname_approximate == (story_year != source_year)


def test_historical_percentages_and_exact_age():
    record = generate_names(age=100, exact_age=True, as_of=date(2000, 2, 29), category="female")[0]
    assert record.birthday == date(1900, 2, 28)
    assert record.first_name_year == 1900 and record.category == "female"


@pytest.mark.parametrize("generator", [generate_names, generate_people])
@pytest.mark.parametrize(
    "kwargs", [{"category": "bogus"}, {"name_fallback": "silent"}, {"count": 0}]
)
def test_invalid_name_options(generator, kwargs):
    with pytest.raises(ValueError):
        generator(age=42, as_of=REFERENCE, **kwargs)


def test_invalid_fnr_sex_filter():
    with pytest.raises(ValueError, match="sex"):
        generate_fnrs(age=42, as_of=REFERENCE, sex="bogus")

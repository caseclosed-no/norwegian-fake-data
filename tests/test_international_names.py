import csv
import io
import json
from collections import Counter
from datetime import date

import pytest
from rich.text import Text
from typer.testing import CliRunner

from norwegian_fake_data import generate_names, generate_people, name_profiles
from norwegian_fake_data.cli import app

REFERENCE = date(2026, 11, 2)


def test_norwegian_seeded_results_are_preserved():
    assert [r.name for r in generate_names(5, age=42, as_of=REFERENCE, seed=73)] == [
        "Siren Olsen",
        "Ragnhild Johansen",
        "Sigrid Mathisen",
        "Nina Daleng",
        "Ole Andersen",
    ]
    people = generate_people(2, age=42, as_of=REFERENCE, seed=73)
    assert [(p.name, p.fnr, p.phone) for p in people] == [
        ("Trude Gulliksen", "17108422867", "68 05 33 92"),
        ("Ragnhild Johansen", "26058429465", "68 05 90 07"),
    ]


@pytest.mark.parametrize("locale,start,stop", [("us", 1880, 2025), ("england", 1996, 2024)])
def test_bundled_international_distributions(locale, start, stop):
    data = name_profiles.snapshot(locale)
    assert name_profiles.years(locale, "first_names") == tuple(range(start, stop + 1))
    for section in ("first_names", "surnames", "historical", "occupational"):
        for rows in data.get(section, {}).values():
            assert rows and len({n for n, _ in rows}) == len(rows)
            assert all(n and isinstance(w, int) and w > 0 for n, w in rows)
    assert all(len(source["sha256"]) == 64 for source in data["sources"].values())
    if locale == "us":
        assert len(data["surnames"]["2020"]) == 156621
        assert dict(data["first_names"]["2025:male"])["Liam"] == 20818
    else:
        assert len(data["surnames"]["curated"]) == 500
        assert len(data["occupational"]) == 24 * 2 * 7
        assert any("10%" in note for note in data["occupational_notes"])


@pytest.mark.parametrize("locale", ["us", "england"])
@pytest.mark.parametrize("category", ["male", "female", "either"])
def test_locale_sampling_and_repeatability(locale, category):
    options = dict(age=20, as_of=REFERENCE, name_locale=locale, category=category, seed=73)
    records = generate_names(30, **options)
    assert records == generate_names(30, **options)
    for record in records:
        assert record.first_name_year == record.birthday.year
        assert record.name_locale == locale
        assert record.first_name in dict(
            name_profiles.snapshot(locale)["first_names"][
                f"{record.birthday.year}:{record.category}"
            ]
        )
        assert record.background_applied == "any"
        if locale == "england":
            assert record.surname_year is None and record.surname_approximate
            assert record.source_geography == "England and Wales"
            assert record.surname_method == "curated_weights"
        else:
            assert record.surname_year == 2020 and record.surname_approximate


@pytest.mark.parametrize(
    "background,classes",
    [
        ("lower", (5, 6, 7)),
        ("middle", (3, 4)),
        ("higher", (1, 2)),
    ],
)
def test_england_background_sums_original_counts(background, classes):
    rows, meta = name_profiles.distribution(
        "england", 2006, "female", "error", background, None, "error"
    )
    expected = Counter()
    for cls in classes:
        expected.update(
            dict(name_profiles.snapshot("england")["occupational"][f"2006:female:{cls}"])
        )
    assert dict(rows) == expected
    assert meta["background_applied"] == background
    assert meta["background_method"] == "parental_occupation_counts"
    record = generate_names(
        birthday=date(2006, 1, 1),
        name_locale="england",
        background=background,
        category="female",
        as_of=REFERENCE,
        seed=73,
    )[0]
    assert record.first_name in expected


def test_individual_nssec_class():
    record = generate_names(
        birthday=date(2006, 1, 1), name_locale="england", nssec=7, as_of=REFERENCE
    )[0]
    assert record.background == "any" and record.background_applied == "nssec-7"
    assert record.nssec == 7
    assert record.first_name in dict(
        name_profiles.snapshot("england")["occupational"][f"2006:{record.category}:7"]
    )


@pytest.mark.parametrize("year,expected", [(1971, 1974), (1969, 1964), (1904, 1904), (1854, 1904)])
def test_historical_ranks_are_explicit_and_flagged(year, expected):
    options = dict(birthday=date(year, 1, 1), name_locale="england", as_of=REFERENCE)
    with pytest.raises(ValueError, match="historical"):
        generate_names(**options)
    record = generate_names(**options, name_fallback="historical")[0]
    assert record.first_name_year == expected and record.first_name_approximate
    assert record.sampling_method == "historical_rank"
    assert "1/rank" in record.approximation_reasons
    nearest = generate_names(**options, name_fallback="nearest")[0]
    assert nearest.first_name_year == 1996


@pytest.mark.parametrize("locale,year", [("england", 1984), ("us", 2020)])
def test_background_fallback_is_explicit(locale, year):
    options = dict(
        birthday=date(year, 1, 1),
        as_of=REFERENCE,
        name_locale=locale,
        name_fallback="nearest",
        background="higher",
        seed=73,
    )
    with pytest.raises(ValueError, match="background-fallback"):
        generate_names(**options)
    record = generate_names(**options, background_fallback="unconditioned")[0]
    assert record.background == "higher" and record.background_applied == "any"
    assert "not applied" in record.approximation_reasons


@pytest.mark.parametrize("seed", range(3))
def test_entire_age_pool_is_validated_for_background(seed):
    with pytest.raises(ValueError, match="2001–2024"):
        generate_names(
            age=25, as_of=REFERENCE, seed=seed, name_locale="england", background="lower"
        )


def test_sni_tertiles_keep_ties_and_missing_scores_out():
    rows = [("A", 1), ("B", 1), ("C", 1), ("Missing", 1)]
    groups, mass, cutoffs = name_profiles.score_groups(rows, {"a": 0.1, "b": 0.5, "c": 0.9})
    assert groups == {"lower": [["A", 1]], "middle": [["B", 1]], "higher": [["C", 1]]}
    assert mass == 0.75 and cutoffs == (0.1, 0.5)
    with pytest.raises(ValueError, match="75%"):
        name_profiles.score_groups(rows, {"a": 0.1, "b": 0.5})
    with pytest.raises(ValueError, match="nonempty"):
        name_profiles.score_groups(rows[:3], {"a": 0.5, "b": 0.5, "c": 0.5})


@pytest.mark.parametrize("background", ["lower", "middle", "higher"])
def test_us_background_scores_and_coverage(background):
    record = generate_names(
        birthday=date(1984, 1, 1),
        name_locale="us",
        background=background,
        category="female",
        as_of=REFERENCE,
        seed=73,
    )[0]
    assert record.first_name_approximate
    assert record.background_method == "experimental_sni_tertiles"
    assert record.background_geography == "California"
    assert record.background_period == "1982–2017" and record.background_matched_mass >= 0.75
    low, high = map(float, record.background_cutoffs.split(","))
    score = name_profiles.snapshot("us")["ses_scores"][record.first_name.casefold()]
    assert {"lower": score <= low, "middle": low < score <= high, "higher": score > high}[
        background
    ]


@pytest.mark.parametrize(
    "options",
    [
        {"name_locale": "uk"},
        {"background": "rich"},
        {"background_fallback": "nearest"},
        {"background": "lower"},
        {"nssec": 1},
        {"name_fallback": "historical"},
        {"name_locale": "england", "nssec": 8},
        {"name_locale": "england", "nssec": True},
        {"name_locale": "england", "nssec": 1, "background": "lower"},
    ],
)
def test_invalid_options(options):
    with pytest.raises(ValueError):
        generate_names(age=20, as_of=REFERENCE, **options)


@pytest.mark.parametrize("locale", ["us", "england"])
def test_person_uses_name_locale_and_keeps_norwegian_identifiers(locale):
    people = generate_people(
        10,
        age=20,
        as_of=REFERENCE,
        seed=73,
        name_locale=locale,
        background="middle",
        unique=True,
        vehicle=True,
    )
    for person in people:
        assert person.name_locale == locale and person.background_applied == "middle"
        assert (int(person.fnr[8]) % 2 == 1) == (person.category == "male")
        assert person.phone.startswith("68 05") and person.plate.startswith(("QA", "QB", "QC"))
        assert person.email.isascii() and person.email.endswith("@example.com")


@pytest.mark.parametrize("command", ["name", "person"])
@pytest.mark.parametrize("output", ["json", "csv", "rich", "plain"])
def test_international_cli_exports(command, output):
    result = CliRunner().invoke(
        app,
        [
            command,
            "--birthday",
            "2006",
            "1",
            "1",
            "--name-locale",
            "england",
            "--nssec",
            "1",
            "--format",
            output,
            "--seed",
            "73",
        ],
    )
    assert result.exit_code == 0, result.output
    if output == "json":
        row = json.loads(result.stdout)[0]
        assert row["surname_year"] is None
    elif output == "csv":
        row = next(csv.DictReader(io.StringIO(result.stdout)))
        assert row["surname_year"] == ""
    else:
        assert result.stdout.strip()
        return
    assert row["name_locale"] == "england" and row["background_applied"] == "nssec-1"
    assert row["source_geography"] == "England and Wales"


@pytest.mark.parametrize("color", ["0", "1"])
def test_cli_background_failure_has_no_partial_output(color):
    result = CliRunner().invoke(
        app,
        [
            "name",
            "--age",
            "42",
            "--as-of",
            "2026-11-02",
            "--name-locale",
            "england",
            "--background",
            "higher",
            "--name-fallback",
            "historical",
        ],
        env={"FORCE_COLOR": color, "TERM": "xterm-256color"},
    )
    assert result.exit_code == 2 and not result.stdout
    assert "background-fallback" in Text.from_ansi(result.stderr).plain

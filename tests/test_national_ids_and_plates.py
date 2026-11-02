import csv
import io
import json
import random
import re
from datetime import date

import pytest
from rich.text import Text
from typer.testing import CliRunner

from norwegian_fake_data import (
    generate_ninos,
    generate_people,
    generate_plate_records,
    generate_plates,
    generate_ssns,
)
from norwegian_fake_data.cli import app

REFERENCE = date(2026, 11, 2)
runner = CliRunner()


@pytest.mark.parametrize(
    "generator,key,pattern",
    [
        (generate_ssns, "ssn", r"000-\d{2}-\d{4}"),
        (generate_ninos, "nino", r"QQ \d{2} \d{2} \d{2} [A-D]"),
    ],
)
def test_national_id_structure_guarantee_and_compact(generator, key, pattern):
    records = generator(200, seed=73, unique=True)
    assert all(re.fullmatch(pattern, getattr(r, key), re.ASCII) for r in records)
    assert len({getattr(r, key) for r in records}) == 200
    compact = generator(200, seed=73, unique=True, compact=True)
    assert [getattr(r, key).replace(" ", "").replace("-", "") for r in records] == [
        getattr(r, key) for r in compact
    ]
    assert all(r.invalid_reason and r.fictional_method and r.source_url for r in records)
    assert all(r.verified_on == "2026-11-02" for r in records)


def test_nino_uniqueness_does_not_reuse_digits_with_another_suffix():
    records = generate_ninos(100_000, seed=1, unique=True, compact=True)
    assert len({r.nino[:-1] for r in records}) == len(records)
    assert {r.nino[-1] for r in records} == set("ABCD")


@pytest.mark.parametrize(
    "generator,key,last",
    [
        (generate_ssns, "ssn", "000999999"),
        (generate_ninos, "nino", "QQ999999A"),
    ],
)
def test_number_pool_boundaries_preserve_leading_zeros(monkeypatch, generator, key, last):
    class BoundaryRandom:
        def choice(self, pool):
            return pool[0] if isinstance(pool, str) else pool[-1]

    monkeypatch.setattr(
        "norwegian_fake_data.national_ids.random.Random", lambda _: BoundaryRandom()
    )
    assert getattr(generator(compact=True)[0], key) == last


def test_norwegian_plate_seed_and_import_path_are_preserved():
    from norwegian_fake_data.identifiers import generate_plates as original_import

    expected = ["QB 66703", "QA 74073", "QC 93266", "QC 81775", "QB 16016"]
    assert generate_plates(5, seed=73) == expected
    assert original_import(5, seed=73) == expected
    records = generate_plate_records(5, seed=73, as_of=REFERENCE)
    assert [r.plate for r in records] == expected
    assert all(r.locale == "no" and r.fictional_method == "reviewed_absent_prefix" for r in records)


def test_california_exhaustive_unique_pool_is_deleted_series_only():
    records = generate_plate_records(
        27_000, locale="us", state="ca", unique=True, seed=73, as_of=REFERENCE
    )
    expected = {
        f"{digit}{letters}{number:03d}"
        for digit in range(1, 10)
        for letters in ("SAM", "FAN", "GAT")
        for number in range(1000)
    }
    assert {r.plate for r in records} == expected
    for r in records:
        assert r.state == "CA" and r.locale == "us" and r.vehicle_class == "passenger"
        assert r.fictional_method == "dmv_deleted_letter_block"
        assert "regular and personalized" in r.invalid_reason
        assert r.plate_style == "california_legacy_passenger"
    with pytest.raises(ValueError, match="27,000"):
        generate_plates(27_001, locale="us", state="CA", unique=True)


@pytest.mark.parametrize(
    "registered,code",
    [
        (date(2001, 9, 1), "51"),
        (date(2002, 2, 28), "51"),
        (date(2002, 3, 1), "02"),
        (date(2024, 2, 29), "73"),
        (date(2026, 2, 28), "75"),
        (date(2026, 3, 1), "26"),
        (date(2026, 8, 31), "26"),
        (date(2026, 9, 1), "76"),
        (date(2050, 2, 28), "99"),
        (date(2050, 3, 1), "50"),
        (date(2050, 8, 31), "50"),
    ],
)
def test_gb_age_identifiers_and_fixed_invalid_regional_tag(registered, code):
    record = generate_plate_records(locale="uk", registered_on=registered, as_of=date(2050, 8, 31))[
        0
    ]
    assert record.plate.startswith(f"ZZ{code} ")
    assert re.fullmatch(r"ZZ\d{2} [A-HJ-PR-Z]{3}", record.plate)
    assert record.registered_on == registered and record.region == "gb"
    assert record.fictional_method == "invalid_zz_regional_tag"
    assert record.date_source_url and record.source_url


def test_gb_exhaustive_unique_pool_and_compact():
    capacity = 24**3
    options = dict(locale="uk", region="GB", as_of=REFERENCE, seed=73, unique=True)
    records = generate_plate_records(capacity, **options)
    expected_letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - {"I", "Q"}
    assert len({r.plate for r in records}) == capacity
    assert {r.plate[-3:] for r in records} == {
        a + b + c for a in expected_letters for b in expected_letters for c in expected_letters
    }
    assert all(r.plate.startswith("ZZ76 ") for r in records)
    assert generate_plates(10, compact=True, **options) == [
        p.replace(" ", "") for p in generate_plates(10, **options)
    ]
    with pytest.raises(ValueError, match="13,824"):
        generate_plates(capacity + 1, **options)


@pytest.mark.parametrize(
    "options,fragment",
    [
        ({"locale": "gb"}, "locale"),
        ({"locale": "us"}, "state"),
        ({"locale": "us", "state": "NY"}, "not supported"),
        ({"locale": "us", "state": "TX"}, "not supported"),
        ({"locale": "us", "state": "CA", "prefix": "SAM"}, "prefix"),
        ({"locale": "uk", "prefix": "AB"}, "prefix"),
        ({"locale": "uk", "region": "ni"}, "Northern Ireland"),
        ({"locale": "uk", "state": "CA"}, "state"),
        ({"region": "gb"}, "region"),
        ({"state": "CA"}, "state"),
        ({"registered_on": REFERENCE}, "registered-on"),
        ({"locale": "us", "state": "CA", "registered_on": REFERENCE}, "registered-on"),
        ({"locale": "us", "state": "CA", "as_of": date(1979, 12, 31)}, "1980"),
        ({"locale": "uk", "registered_on": date(2001, 8, 31)}, "2001-09-01"),
        (
            {"locale": "uk", "registered_on": date(2050, 9, 1), "as_of": date(2051, 1, 1)},
            "2050-08-31",
        ),
        ({"locale": "uk", "registered_on": date(2026, 11, 3)}, "after"),
    ],
)
def test_plate_requests_reject_unverified_or_inconsistent_options(options, fragment):
    options = {"as_of": REFERENCE, **options}
    with pytest.raises(ValueError, match=fragment):
        generate_plate_records(**options)


@pytest.mark.parametrize(
    "generator,options",
    [
        (generate_ssns, {}),
        (generate_ninos, {}),
        (generate_plate_records, {"locale": "us", "state": "CA", "as_of": REFERENCE}),
        (generate_plate_records, {"locale": "uk", "as_of": REFERENCE}),
    ],
)
def test_seed_rng_isolation_and_count_validation(generator, options):
    state = random.getstate()
    assert generator(20, seed=73, **options) == generator(20, seed=73, **options)
    assert generator(20, seed=73, **options) != generator(20, seed=74, **options)
    assert random.getstate() == state
    for count in (0, -1, 100_001):
        with pytest.raises(ValueError, match="count"):
            generator(count, **options)


@pytest.mark.parametrize("locale", ["us", "uk", "invalid"])
def test_person_locale_rejects_unsupported_full_records(locale):
    with pytest.raises(ValueError, match="locale|phone profiles"):
        generate_people(age=42, locale=locale, as_of=REFERENCE)


@pytest.mark.parametrize(
    "command,options,key,locale",
    [
        ("ssn", [], "ssn", "us"),
        ("nino", [], "nino", "uk"),
        ("plate", ["--locale", "us", "--state", "CA"], "plate", "us"),
        ("plate", ["--locale", "uk", "--registered-on", "2022-04-18"], "plate", "uk"),
    ],
)
@pytest.mark.parametrize("output", ["plain", "json", "csv", "rich"])
def test_cli_output_formats(command, options, key, locale, output):
    args = [command, *options, "--count", "3", "--unique", "--seed", "73", "--format", output]
    if command == "plate":
        args += ["--as-of", "2026-11-02"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert not result.stderr
    if output == "plain":
        assert len(result.stdout.splitlines()) == 3
        assert "\t" not in result.stdout
    elif output == "rich":
        assert key.title() in result.stdout
    else:
        rows = (
            json.loads(result.stdout)
            if output == "json"
            else list(csv.DictReader(io.StringIO(result.stdout)))
        )
        assert len(rows) == 3 and len({r[key] for r in rows}) == 3
        assert all(r["locale"] == locale and r["invalid_reason"] and r["source_url"] for r in rows)
        if locale == "uk" and key == "plate":
            assert all(
                r[key].startswith("ZZ22 ") and r["registered_on"] == "2022-04-18" for r in rows
            )


@pytest.mark.parametrize("color", ["0", "1"])
@pytest.mark.parametrize(
    "args,fragment",
    [
        (["plate", "--locale", "us"], "--state"),
        (["plate", "--locale", "us", "--state", "TX"], "not supported"),
        (["plate", "--locale", "uk", "--region", "ni"], "Northern Ireland"),
        (["plate", "--locale", "uk", "--registered-on", "2026-02-30"], "calendar date"),
        (["plate", "--locale", "uk", "--registered-on", "20260418"], "YYYY-MM-DD"),
        (
            ["plate", "--locale", "uk", "--registered-on", "2026-11-03", "--as-of", "2026-11-02"],
            "after",
        ),
        (["plate", "--locale", "us", "--state", "CA", "--count", "27001", "--unique"], "27,000"),
        (["person", "--locale", "us", "--age", "42"], "phone profiles"),
        (["ssn", "--mode", "valid"], "No such option"),
        (["nino", "--prefix", "AB"], "No such option"),
    ],
)
def test_cli_errors_have_no_partial_output(args, fragment, color):
    result = runner.invoke(app, args, env={"FORCE_COLOR": color, "TERM": "xterm-256color"})
    assert result.exit_code == 2 and not result.stdout
    assert fragment in Text.from_ansi(result.stderr).plain
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("command", ["ssn", "nino", "plate", "person"])
def test_new_command_help(command):
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0 and "Usage" in result.stdout


def test_gb_default_registration_date_is_story_date():
    record = generate_plate_records(locale="uk", as_of=REFERENCE)[0]
    assert record.registered_on == REFERENCE
    assert record.plate.startswith("ZZ76 ")


def test_new_generators_work_without_network(monkeypatch):
    def unavailable(*args, **kwargs):
        raise AssertionError("Generation must not use the network")

    monkeypatch.setattr("socket.socket", unavailable)
    assert generate_ssns() and generate_ninos()
    assert generate_plates(locale="us", state="CA", as_of=REFERENCE)
    assert generate_plates(locale="uk", as_of=REFERENCE)

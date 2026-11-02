import csv
import io
import json
import random
import re

import pytest
from rich.text import Text
from typer.testing import CliRunner

from norwegian_fake_data import (
    generate_phone_records,
    generate_phones,
    generate_wallet_address_records,
    generate_wallet_addresses,
)
from norwegian_fake_data.cli import app
from norwegian_fake_data.phones import UK_LANDLINES, US_AREA_CODES

runner = CliRunner()


@pytest.mark.parametrize("area", US_AREA_CODES)
def test_us_entire_reserved_pool(area):
    values = generate_phones(100, locale="us", area_code=area, unique=True, style="compact")
    assert set(values) == {f"{area}555{line:04d}" for line in range(100, 200)}
    with pytest.raises(ValueError, match="100"):
        generate_phones(101, locale="us", area_code=area, unique=True)


# Independent expected boundaries from Ofcom's published table.
@pytest.mark.parametrize(
    "city,start",
    [
        ("leeds", "01134960000"),
        ("sheffield", "01144960000"),
        ("nottingham", "01154960000"),
        ("leicester", "01164960000"),
        ("bristol", "01174960000"),
        ("reading", "01184960000"),
        ("birmingham", "01214960000"),
        ("edinburgh", "01314960000"),
        ("glasgow", "01414960000"),
        ("liverpool", "01514960000"),
        ("manchester", "01614960000"),
        ("london", "02079460000"),
        ("tyneside", "01914980000"),
        ("northern-ireland", "02896496000"),
        ("cardiff", "02920180000"),
        ("generic", "01632960000"),
        (None, "07700900000"),
    ],
)
def test_uk_entire_reserved_pool(city, start):
    options = {"kind": "landline", "city": city} if city else {}
    values = generate_phones(1000, locale="uk", unique=True, style="compact", **options)
    assert set(values) == {str(int(start) + n).zfill(11) for n in range(1000)}
    with pytest.raises(ValueError, match="1,000"):
        generate_phones(1001, locale="uk", unique=True, **options)


@pytest.mark.parametrize(
    "options,country",
    [
        ({}, "+47"),
        ({"locale": "us"}, "+1"),
        ({"locale": "uk"}, "+44"),
        *[({"locale": "uk", "kind": "landline", "city": city}, "+44") for city in UK_LANDLINES],
    ],
)
def test_phone_formatting_and_seed(options, country):
    domestic = generate_phones(10, seed=7, style="compact", **options)
    spaced = generate_phones(10, seed=7, **options)
    international = generate_phones(10, seed=7, international=True, **options)
    compact = generate_phones(10, seed=7, international=True, style="compact", **options)
    assert [v.replace(" ", "") for v in spaced] == domestic
    expected = [country + (v[1:] if country == "+44" else v) for v in domestic]
    assert compact == expected == [v.replace(" ", "") for v in international]
    assert all(not v.startswith("+44 0") for v in international)


def test_documented_spacing_and_defaults():
    assert re.fullmatch(r"212 555 01\d{2}", generate_phones(locale="us")[0])
    assert re.fullmatch(r"07700 900\d{3}", generate_phones(locale="uk")[0])
    assert re.fullmatch(
        r"020 7946 0\d{3}", generate_phones(locale="uk", kind="landline", city="London")[0]
    )
    assert re.fullmatch(r"01632 960\d{3}", generate_phones(locale="uk", kind="landline")[0])
    assert generate_phones(3, seed=73) == ["68 05 45 84", "68 05 20 02", "68 05 82 27"]


@pytest.mark.parametrize(
    "options",
    [
        {"locale": "xx"},
        {"style": "xx"},
        {"area_code": "212"},
        {"kind": "mobile"},
        {"city": "london"},
        {"locale": "us", "kind": "mobile"},
        {"locale": "us", "city": "london"},
        {"locale": "us", "area_code": "416"},
        {"locale": "us", "area_code": ""},
        {"locale": "uk", "area_code": "212"},
        {"locale": "uk", "city": "london"},
        {"locale": "uk", "kind": "other"},
        {"locale": "uk", "kind": "landline", "city": "paris"},
    ],
)
def test_phone_rejects_invalid_options(options):
    with pytest.raises(ValueError):
        generate_phones(**options)


@pytest.mark.parametrize(
    "chain,prefix,length",
    [
        ("ethereum", "0x", 42),
        ("bitcoin", "bc1q", 42),
        ("monero", "4", 95),
    ],
)
def test_wallets_fail_independent_decoding(chain, prefix, length):
    values = generate_wallet_addresses(1000, chain=chain, seed=12, unique=True)
    assert len(set(values)) == 1000
    assert values == generate_wallet_addresses(1000, chain=chain, seed=12, unique=True)
    for value in values:
        assert len(value) == length and value.startswith(prefix)
        if chain == "ethereum":
            with pytest.raises(ValueError):
                bytes.fromhex(value[2:])
            assert re.fullmatch(r"0x[0-9a-f]{20}g[0-9a-f]{19}", value)
        elif chain == "bitcoin":
            # Decode Bech32 symbols using BIP-173's reference character table.
            table = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
            with pytest.raises(ValueError):
                [table.index(char) for char in value[value.rfind("1") + 1 :]]
            assert value.count("b") == 2  # HRP and the forbidden body symbol.
        else:
            # Base58 decoding cannot map the injected zero to a digit.
            alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            with pytest.raises(ValueError):
                [alphabet.index(char) for char in value]
            assert value.count("0") == 1
    record = generate_wallet_address_records(chain=chain, seed=12, unique=True)[0]
    assert record.chain == chain and record.fictional_method == "forbidden_character"
    assert record.source_url.startswith("https://") and record.invalid_reason


def test_generators_do_not_change_global_rng():
    before = random.getstate()
    generate_phones(locale="uk")
    generate_wallet_addresses(chain="bitcoin")
    assert random.getstate() == before


@pytest.mark.parametrize("count", [0, -1, 100001])
def test_count_limits(count):
    with pytest.raises(ValueError):
        generate_wallet_addresses(count, chain="ethereum")
    with pytest.raises(ValueError):
        generate_phones(count, locale="uk")


def test_wallet_unknown_chain_and_max_unique():
    with pytest.raises(ValueError, match="chain"):
        generate_wallet_addresses(chain="dogecoin")
    assert len(set(generate_wallet_addresses(100000, chain="ethereum", unique=True))) == 100000


@pytest.mark.parametrize(
    "args,key",
    [
        (["phone", "--locale", "us", "--area-code", "415"], "phone"),
        (["phone", "--locale", "uk"], "phone"),
        (["phone", "--locale", "uk", "--kind", "landline", "--city", "london"], "phone"),
        *[(["wallet", "--chain", chain], "address") for chain in ("ethereum", "bitcoin", "monero")],
    ],
)
@pytest.mark.parametrize("format", ["json", "csv", "plain", "rich"])
def test_cli_formats(args, key, format):
    result = runner.invoke(app, [*args, "--count", "3", "--seed", "42", "--format", format])
    assert result.exit_code == 0, result.output
    if format == "json":
        rows = json.loads(result.stdout)
        assert len(rows) == 3 and rows[0][key]
        assert rows[0]["source_url"] and rows[0]["fictional_method"]
    elif format == "csv":
        rows = list(csv.DictReader(io.StringIO(result.stdout)))
        assert len(rows) == 3 and rows[0][key] and rows[0]["verified_on"]
    elif format == "plain":
        assert len(result.stdout.splitlines()) == 3
    else:
        assert key.title() in Text.from_ansi(result.stdout).plain


@pytest.mark.parametrize(
    "args",
    [
        ["wallet"],
        ["wallet", "--chain", "dogecoin"],
        ["phone", "--locale", "us", "--count", "101", "--unique"],
        ["phone", "--locale", "uk", "--city", "london"],
        ["phone", "--area-code", "415"],
    ],
)
def test_cli_errors_have_no_partial_output(args):
    result = runner.invoke(app, args)
    assert result.exit_code == 2
    assert not result.stdout


def test_phone_provenance_and_string_api_agree():
    for locale in ("no", "us", "uk"):
        records = generate_phone_records(5, locale=locale, seed=42)
        assert [r.phone for r in records] == generate_phones(5, locale=locale, seed=42)
        assert all(r.locale == locale and r.source_url and r.verified_on for r in records)

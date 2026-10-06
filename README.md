# Norwegian Fake Data

A Python CLI for making Norwegian phone numbers, fødselsnummer, license plates,
and character records for murder mystery games and props. Runs offline, with Rich
terminal output and JSON/CSV exports.

## Proudly sponsored by CaseClosed

Proudly sponsored by [CaseClosed](https://caseclosed.no) in Norway and
[Caseclosed Mysteries](https://caseclosedmysteries.com) internationally,
creators of printed murder mystery games.

## Get started

You'll need Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).
From this checkout:

```console
uv run norwegian-fake-data phone
uv run norwegian-fake-data fnr --birthday 1987 5 17
uv run norwegian-fake-data plate --count 5
uv run norwegian-fake-data person --age 42 --vehicle
```

Once published to PyPI, use `uvx norwegian-fake-data` from any directory, or
install it with `uv tool install norwegian-fake-data`. Until then, you can run
`uvx --from . norwegian-fake-data` from the checkout.

The examples below use the installed command. Add `uv run` to run them locally.

## Phone numbers

```console
norwegian-fake-data phone --count 10 --unique
norwegian-fake-data phone --international
norwegian-fake-data phone --international --style compact
```

Numbers come from Nkom's reserved TV/film range, `68050000–68059999`.
Choose spaced output (`68 05 12 34`) or compact output (`68051234`), with an
optional `+47` prefix.

## Fødselsnummer

Choose a birthday or an age:

```console
norwegian-fake-data fnr --birthday 1987 5 17
norwegian-fake-data fnr --age 35 --as-of 2026-10-06
norwegian-fake-data fnr --age 35 --exact-age --as-of 2026-10-06
```

`--age 35` picks a random birthday for someone aged 35 on the reference date.
On `2026-10-06`, that's between `1990-10-07` and `1991-10-06`.
`--exact-age` instead uses `1991-10-06`: their 35th birthday is on that date.
`--as-of` defaults to today; set it to the date of your story.

Both modes produce fictional identifiers:

| Mode | Result |
| --- | --- |
| `prop` (default) | Realistic birth date with a deliberately invalid checksum |
| `synthetic` | Month increased by 80, following Skatteetaten's test-data convention |

```console
norwegian-fake-data fnr --birthday 1987 5 17 --mode synthetic
```

Supported birth years are 1854–2039. February 29 birthdays advance in age on
February 28 in non-leap years. JSON and CSV include the actual birthday, age,
mode, and reference date alongside the number.

## License plates

```console
norwegian-fake-data plate --count 5 --unique
norwegian-fake-data plate --prefix QB
norwegian-fake-data plate --prefix QC --compact
```

Plates use `QA`, `QB`, or `QC` followed by five digits, such as `QB 12345`.
These prefixes were absent from Statens vegvesen's published plate series when
checked on 2026-10-06; they are not an officially reserved film range.

## Character records

```console
norwegian-fake-data person --age 42 --count 6 --unique --vehicle \
  --as-of 2024-11-15 --seed 73 --format json > characters.json
```

Each record contains a Norwegian name, birthday, age, FNR, phone, `example.com`
email, and optional plate. It accepts the same birthday and mode options as `fnr`.
Save the records to reuse the same details across letters, contact lists, and
witness statements. Names are drawn from a small hand-curated list and may repeat.

## Output options

| Option | What it does |
| --- | --- |
| `--count N`, `-n N` | Generate a batch; default 1 |
| `--seed N` | Repeat results with the same options and package version |
| `--unique` | Avoid duplicate identifiers within the batch |
| `--format rich` | Tables and character cards |
| `--format plain` | One identifier per line; tab-separated fields for people |
| `--format json` | Array of records |
| `--format csv` | Header and one row per record |

Output defaults to Rich in a terminal and plain text when piped. Use a fixed
`--as-of` with seeded age-based generation. Import identifier columns as text
when opening CSV files in a spreadsheet to keep leading zeros.

```console
norwegian-fake-data phone --count 20 --format csv > phones.csv
norwegian-fake-data --help
norwegian-fake-data fnr --help
```

## Using it from Python

```python
from datetime import date
from norwegian_fake_data import generate_fnrs, generate_people, generate_phones, generate_plates

phones = generate_phones(5, seed=42, unique=True)
plates = generate_plates(5, seed=42, prefix="QA")
records = generate_fnrs(age=35, as_of=date(2026, 10, 6), seed=42)
characters = generate_people(6, age=42, seed=73, vehicle=True, unique=True)

print(records[0].fnr, records[0].birthday)
```

## Data sources

- [Nkom's numbering plan](https://nkom.no/telefoni-og-telefonnummer/telefonnummer-og-den-norske-nummerplan/alle-nummerserier-for-norske-telefonnumre): the TV/film phone range.
- [Statens vegvesen's plate series](https://www.vegvesen.no/kjoretoy/eie-og-vedlikeholde/skilt/skiltserier/): plate format and prefix selection.
- [Skatteetaten's test-data documentation](https://skatteetaten.github.io/folkeregisteret-api-dokumentasjon/test-for-konsumenter/): the synthetic month offset.
- [Skatteetaten's checksum documentation](https://skatteetaten.github.io/folkeregisteret-api-dokumentasjon/nytt-fodselsnummer-fra-2032/): checksum calculations. Prop mode changes the final checksum, which fails both the traditional and published 2032 rules.

## Development and publishing

```console
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
uv run twine check --strict dist/*
```

CI runs lint, tests, and the package build once on Ubuntu with Python 3.11.
Publishing a GitHub release tagged `v<VERSION>` runs the checks and uploads the
built package to PyPI. The tag must match `pyproject.toml`; run `uv lock` after
updating the version.

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
from `caseclosed-no/norwegian-fake-data` through `release.yml`.

## License

[MIT](LICENSE), copyright LVL UP AS.

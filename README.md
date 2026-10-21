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
Run commands with `uvx`, without a permanent installation:

```console
uvx norwegian-fake-data phone
uvx norwegian-fake-data fnr --birthday 1987 5 17
uvx norwegian-fake-data plate --count 5
uvx norwegian-fake-data person --age 42 --vehicle
uvx norwegian-fake-data name --age 70 --as-of 2026-10-21 --count 10
```

For a permanent installation, use `uv tool install norwegian-fake-data`.
To pin a release, use `uvx norwegian-fake-data@0.2.0 phone`.

## Phone numbers

```console
uvx norwegian-fake-data phone --count 10 --unique
uvx norwegian-fake-data phone --international
uvx norwegian-fake-data phone --international --style compact
```

Numbers come from Nkom's reserved TV/film range, `68050000–68059999`.
Choose spaced output (`68 05 12 34`) or compact output (`68051234`), with an
optional `+47` prefix.

## Fødselsnummer

Choose a birthday or an age:

```console
uvx norwegian-fake-data fnr --birthday 1987 5 17
uvx norwegian-fake-data fnr --age 35 --as-of 2026-10-06
uvx norwegian-fake-data fnr --age 35 --exact-age --as-of 2026-10-06
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
uvx norwegian-fake-data fnr --birthday 1987 5 17 --mode synthetic
```

Supported birth years are 1854–2039. February 29 birthdays advance in age on
February 28 in non-leap years. JSON and CSV include the actual birthday, age,
mode, and reference date alongside the number.

## License plates

```console
uvx norwegian-fake-data plate --count 5 --unique
uvx norwegian-fake-data plate --prefix QB
uvx norwegian-fake-data plate --prefix QC --compact
```

Plates use `QA`, `QB`, or `QC` followed by five digits, such as `QB 12345`.
These prefixes were absent from Statens vegvesen's published plate series when
checked on 2026-10-06; they are not an officially reserved film range.

## Names by age

```console
uvx norwegian-fake-data name --age 70 --as-of 2026-10-21 --count 10
uvx norwegian-fake-data name --birthday 1987 5 17 --category female
uvx norwegian-fake-data name --age 42 --as-of 2024-11-15 --seed 73 --format json
```

Names use bundled statistics from Statistics Norway (SSB), with no network calls.
First names are sampled in proportion to the published percentage for the actual
birth year, after resolving `--age` and `--as-of`. First-name coverage is
1880–2025. `--category female`, `male`, or `either` selects SSB's girls' or boys'
name categories; `either` is the default and chooses categories equally for the
standalone `name` command. Names are sampled with replacement and may repeat or
coincide with real names. No uniqueness option is provided for names.

Surnames are independently sampled in proportion to their population counts,
using the nearest available snapshot to the **story date** (2018–2025). These
are population frequencies, not surname distributions by birth cohort. A story
set before 2018 therefore uses 2018 surname frequencies as an approximation.
First-name and surname combinations do not model family, regional, or cultural
relationships.

Birth years outside first-name coverage raise an error unless you explicitly
choose `--name-fallback nearest`:

```console
uvx norwegian-fake-data name --birthday 1870 1 1 --as-of 1900-01-01 --name-fallback nearest
```

This keeps the birthday and uses 1880 first-name weights. Age-based requests are
rejected if any possible birthday falls outside coverage, regardless of seed.
The shared birthday options support years 1854–2039. JSON/CSV name records include
the resolved birthday, age, category, `first_name_year`, `surname_year`, and
`first_name_approximate` / `surname_approximate` flags. Flags indicate use of a
source year different from the birth year or story year respectively; they do not
imply that the underlying statistics cover every name. Plain output prints one
full name per line; Rich output shows a table including the source years.

SSB suppresses first-name figures below four and surname counts below 200; its
first-name list includes names with at least 200 bearers in the previous year.
Sampling is conditional on published positive weights, excluding missing,
suppressed, and zero cells. The first-name series uses birth year before 2021
and naming year from 2021 onward. Some SSB labels already contain compound names;
these labels are preserved, but additional given names are not synthesized.

## Character records

```console
uvx norwegian-fake-data person --age 42 --count 6 --unique --vehicle \
  --as-of 2024-11-15 --seed 73 --format json > characters.json
```

Each record contains a Norwegian name, birthday, age, FNR, phone, `example.com`
email, and optional plate. It accepts the same birthday and mode options as `fnr`.
Save the records to reuse the same details across letters, contact lists, and
witness statements. Names use the same SSB weighting as the `name` command, and
accept `--category` and `--name-fallback`. The first-name category matches the
traditional sex encoding in the generated FNR; an explicit category also filters
the FNR pool. `--unique` continues to apply only to identifiers. Structured person
records include the name category, source years, and approximation flags.
Seeded person names differ from releases that used the old hand-curated lists.

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
uvx norwegian-fake-data phone --count 20 --format csv > phones.csv
uvx norwegian-fake-data --help
uvx norwegian-fake-data fnr --help
```

## Using it from Python

```python
from datetime import date
from norwegian_fake_data import generate_fnrs, generate_people, generate_phones, generate_plates

from norwegian_fake_data import generate_names

names = generate_names(10, age=70, as_of=date(2026, 10, 21), category="female", seed=73)
phones = generate_phones(5, seed=42, unique=True)
plates = generate_plates(5, seed=42, prefix="QA")
records = generate_fnrs(age=35, as_of=date(2026, 10, 6), seed=42)
characters = generate_people(6, age=42, seed=73, vehicle=True, unique=True)

print(records[0].fnr, records[0].birthday)
```

## Data sources

- [SSB table 10467](https://www.ssb.no/statbank/table/10467): first-name percentages by year, 1880–2025.
- [SSB table 12891](https://www.ssb.no/statbank/table/12891): surname population counts, 2018–2025.
  SSB statistics are adapted under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/);
  see [the data attribution](src/norwegian_fake_data/data/README.md) for transformations and limitations.

- [Nkom's numbering plan](https://nkom.no/telefoni-og-telefonnummer/telefonnummer-og-den-norske-nummerplan/alle-nummerserier-for-norske-telefonnumre): the TV/film phone range.
- [Statens vegvesen's plate series](https://www.vegvesen.no/kjoretoy/eie-og-vedlikeholde/skilt/skiltserier/): plate format and prefix selection.
- [Skatteetaten's test-data documentation](https://skatteetaten.github.io/folkeregisteret-api-dokumentasjon/test-for-konsumenter/): the synthetic month offset.
- [Skatteetaten's checksum documentation](https://skatteetaten.github.io/folkeregisteret-api-dokumentasjon/nytt-fodselsnummer-fra-2032/): checksum calculations. Prop mode changes the final checksum, which fails both the traditional and published 2032 rules.

## Development and publishing

From a checkout, run the CLI with `uvx --from . norwegian-fake-data` and use
these commands for development:

```console
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
uv run twine check --strict dist/*
```

Refresh the bundled name statistics with `python scripts/update_names.py` (requires
network access). The script records source update dates, retrieval date, and
checksums in the snapshot. Review data changes and run the checks before releasing.
The snapshot uses the existing PxWebApi v1 endpoint; generation itself stays offline.

CI runs lint, tests, and the package build once on Ubuntu with Python 3.11.
Pushing a version tag runs the checks and publishes the package to PyPI.
Set the version in `pyproject.toml`, run `uv lock`, then commit and push before
tagging that commit. For version `0.2.0`:

```console
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0
```

The tag must match the package version. Use a new version and tag for each release.
After publishing, run `uvx --refresh norwegian-fake-data --version` to get the latest.

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
from `caseclosed-no/norwegian-fake-data` through `release.yml`.

## License

Code: [MIT](LICENSE), copyright LVL UP AS.
Bundled SSB statistics: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
attributed to Statistics Norway (SSB).

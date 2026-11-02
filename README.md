# Norwegian Fake Data

A Python CLI for Norwegian fictional identifiers and character records, with
Norwegian, US, and England name sampling for murder mystery games and props.
Runs offline, with Rich terminal output and JSON/CSV exports.

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
To pin a release, use `uvx norwegian-fake-data@0.3.1 phone`.

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

The default Norwegian names use bundled statistics from Statistics Norway (SSB),
with no network calls.
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

## US and England names

Choose a name profile with `--name-locale no|us|england`; `no` remains the default.
All profiles work offline and support `--category`, `--seed`, and JSON/CSV exports.

```console
uvx norwegian-fake-data name --name-locale us --age 42 --as-of 2026-11-02 --count 10
uvx norwegian-fake-data name --name-locale england --age 20 --as-of 2026-11-02 --count 10
uvx norwegian-fake-data name --name-locale england --age 55 --as-of 2026-11-02 \
  --name-fallback historical
```

US first names use SSA birth counts for **1880–2025**, excluding suppressed counts
below five. Early cohorts are incomplete, especially before 1937. Surnames use
the 2020 Census population counts, which include disclosure-avoidance adjustments.
The surname source year is always 2020; other story years are marked approximate.

The England profile uses ONS annual name counts for **1996–2024**. The source
geography is **England and Wales**, not England alone. Older characters require an
explicit fallback: `--name-fallback historical` uses the nearest historical
top-100 list (1904–2024, every ten years), weighted by approximately `1/rank`.
This is a heuristic rather than measured birth frequencies. Ties in source-year
distance choose the earlier year. For years within annual coverage, `historical`
still uses annual counts. It does not approximate future years. The existing
`nearest` option instead selects the nearest annual year for any profile.

England surnames use 500 curated, weighted British surnames adapted from Faker.
They have no verified population snapshot date, so `surname_year` is null in JSON
and blank in CSV, and `surname_approximate` is always true. First names and surnames
are independent: family, regional, and cultural relationships are not modeled.

### Socioeconomic backgrounds

Use `--background lower|middle|higher` to request an optional birth-background
proxy. The default is `any`. These groups do **not** establish a character's current
income, poverty, wealth, or social class, and they have different meanings by source.

```console
uvx norwegian-fake-data name --name-locale england --birthday 2006 1 1 \
  --background higher --as-of 2026-11-02 --count 10
uvx norwegian-fake-data name --name-locale england --birthday 2006 1 1 --nssec 7
uvx norwegian-fake-data name --name-locale us --birthday 1984 1 1 \
  --background lower --as-of 2026-11-02 --format json
```

For England, **2001–2024** ONS name counts are grouped by parents' occupations:
`higher` combines NS-SEC classes 1–2, `middle` classes 3–4, and `lower` classes 5–7.
Counts are summed before sampling. `--nssec 1` through `--nssec 7` selects an
original class instead; it cannot be combined with a non-`any` background.
Approximately 10% of birth records receive NS-SEC codes. The higher parental
class is used when both are known; students and never-worked/long-term-unemployed
categories are excluded. Published cells below three are suppressed. This data
does not cover older English characters or specifically represent the poorest.

For the US, backgrounds are **experimental**, supported for birth years
**1982–2017**. A CC BY 4.0 research dataset supplies a name-level score based on
average residential ZIP-code income percentile in California births. Its core
sample excludes births coded Hispanic or Asian, and its scores pool the entire
period. Only unambiguous, untruncated canonical spellings are matched to SSA names.
Matched names are sorted into SSA-frequency-weighted score thirds for each birth
year and category; equal scores stay together. Sampling keeps the SSA weights
inside the selected group. These are relative name-score groups, not measured
name distributions among poor, middle-income, and rich households.

US exports include `background_matched_mass` and the two SNI `background_cutoffs`.
In the bundled supported cohorts, matched mass ranges from about 85–94% of
published SSA birth counts; distributions below 75% are rejected. Unmatched names
are excluded from background sampling, never assigned a low score.

Unsupported background requests fail before producing output, even if only one
possible birth year in an age request is unsupported. To explicitly omit an
unavailable US/England filter, use `--background-fallback unconditioned`.
Exports retain the requested background, set `background_applied` to `any`, and
explain the fallback. Name-year coverage still requires its own fallback.
Norwegian names do not yet support socioeconomic filtering. Surnames are never
filtered by background.

JSON/CSV records include the requested and applied background, source geography,
sampling method, source year/period, dataset version, and approximation reasons.
`first_name_approximate` also marks historical rank weighting and US score overlays,
even when the source year matches the birthday. Rich name tables show `*` beside
an approximate first-name source year; use JSON/CSV for full provenance.

## Character records

```console
uvx norwegian-fake-data person --age 42 --count 6 --unique --vehicle \
  --as-of 2024-11-15 --seed 73 --format json > characters.json
```

Each record contains a name, birthday, age, FNR, phone, `example.com`
email, and optional plate. It accepts the same birthday and mode options as `fnr`.
Save the records to reuse the same details across letters, contact lists, and
witness statements. By default, names use the same SSB weighting as `name`, and
accept `--category` and `--name-fallback`. The first-name category matches the
traditional sex encoding in the generated FNR; an explicit category also filters
the FNR pool. `--unique` continues to apply only to identifiers. Structured person
records include the name category, source years, and approximation flags.
The `person` command also accepts `--name-locale`, `--background`, `--nssec`, and
`--background-fallback`. These select **names only**: FNRs, phones, and plates
continue to use Norwegian rules. For example:

```console
uvx norwegian-fake-data person --name-locale us --age 42 --as-of 2026-11-02 --seed 73
```

Norwegian seeded names and identifiers are preserved from version 0.2.0.
Version 0.3.1 adds provenance columns to name/person JSON and CSV exports (and
tab-separated person output); consumers should use field names rather than column
positions. `surname_year` is now nullable for curated England surnames.

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
us_names = generate_names(
    10, age=42, as_of=date(2026, 11, 2), name_locale="us", background="higher", seed=73
)
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
- [SSA national names](https://www.ssa.gov/oact/babynames/limits.html): US birth-name counts, 1880–2025.
- [2020 Census name files](https://www.census.gov/topics/population/genealogy/data/2020_names.html): US surname frequencies.
- [ONS annual names](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesinenglandandwalesfrom1996/1996tocurrent),
  [historical names](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesenglandandwalestop100babynameshistoricaldata), and
  [names by parental occupation](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/adhocs/2958babynamesbynationalstatisticssocioeconomicclassificationenglandandwales2001to2024), under OGL v3.0.
- [Weiss, Spitzer, and Nourbash's name scores](https://doi.org/10.7910/DVN/Q3V8OS), under CC BY 4.0.
- [Faker British surname weights](https://github.com/joke2k/faker/blob/685ea97a9fbb4ab36dc32ea4d318498992f7ba7e/faker/providers/person/en_GB/__init__.py), under MIT.
  See [international data attribution and refresh instructions](src/norwegian_fake_data/data/INTERNATIONAL.md).

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
International snapshots are built with
`uv run python scripts/update_international_names.py --source-dir DIR`; see the
international data instructions for cached source filenames and URLs. XLSX parsing
uses a development-only dependency. The US and England snapshots add about 12 MB
to the package.

CI runs lint, tests, and the package build once on Ubuntu with Python 3.11.
Pushing a version tag runs the checks and publishes the package to PyPI.
Set the version in `pyproject.toml`, run `uv lock`, then commit and push before
tagging that commit. For version `0.3.1`:

```console
git tag -a v0.3.1 -m "Release 0.3.1"
git push origin v0.3.1
```

The tag must match the package version. Use a new version and tag for each release.
After publishing, run `uvx --refresh norwegian-fake-data --version` to get the latest.

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
from `caseclosed-no/norwegian-fake-data` through `release.yml`.

## License

Code: [MIT](LICENSE), copyright LVL UP AS.
Bundled SSB statistics: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
attributed to Statistics Norway (SSB).
International statistics and adapted surname lists retain their source licenses;
see [international attribution](src/norwegian_fake_data/data/INTERNATIONAL.md).

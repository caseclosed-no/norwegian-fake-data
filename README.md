# Norwegian Fake Data

A Python CLI for fictional identifiers and character records for murder mystery
games and props. Includes Norwegian identifiers, US Social Security numbers and
California plates, UK National Insurance numbers and GB plates, Norwegian/US/UK
fictional phones, impossible crypto addresses, and Norwegian, US, and England names. Runs offline, with Rich output and JSON/CSV exports.

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
To pin a release, use `uvx norwegian-fake-data@0.5.0 phone`.

## Phone numbers

```console
uvx norwegian-fake-data phone --count 10 --unique
uvx norwegian-fake-data phone --international
uvx norwegian-fake-data phone --international --style compact
```

Numbers come from Nkom's reserved TV/film range, `68050000–68059999`.
Choose spaced output (`68 05 12 34`) or compact output (`68051234`), with an
optional `+47` prefix.

### US and UK phones

Version 0.5.0 adds US and UK fictional phone profiles.

```console
uvx norwegian-fake-data phone --locale us --area-code 212
uvx norwegian-fake-data phone --locale us --area-code 415 --international
uvx norwegian-fake-data phone --locale uk
uvx norwegian-fake-data phone --locale uk --kind landline --city london
uvx norwegian-fake-data phone --locale uk --international --style compact
```

Norway remains the default, with its existing seed results. US output defaults to
area code `212`, with a reserved `555-0100`–`555-0199` suffix (100 unique numbers
per area code). Reviewed area codes are `212`, `213`, `310`, `323`, `408`, `415`,
`424`, `628`, `646`, `650`, `669`, and `917`. This is a curated selection, not a
complete US directory. Other area codes are rejected; arbitrary `555` numbers
outside the reserved block may be real.

UK output defaults to mobile `07700 900000`–`07700 900999`. Choose
`--kind landline` for generic `01632 960000`–`01632 960999`, or supply a city:
`leeds`, `sheffield`, `nottingham`, `leicester`, `bristol`, `reading`, `birmingham`,
`edinburgh`, `glasgow`, `liverpool`, `manchester`, `london`, `tyneside`,
`northern-ireland`, or `cardiff`. `tyneside` also covers Durham/Sunderland.
Each UK profile contains 1,000 unique numbers. City names are case-insensitive;
`northern ireland` is also accepted. A city requires `--kind landline`.

Spaced output uses local grouping, such as `212 555 0123`, `07700 900123`, and
`020 7946 0123`. International output adds `+1` or `+44` and drops the UK's
domestic leading zero (`+44 7700 900123`, compact `+447700900123`).
`--area-code` applies only to US phones; `--kind` and `--city` apply only to UK
phones. Incompatible options and excessive unique counts fail before output.

Phones use regulator-designated fictional ranges and may pass format validators.
They are not structurally invalid strings. Phone JSON/CSV now include locale,
profile, area code/city, fictional method, source URLs, and verification date;
plain output remains one number per line.

## Impossible crypto addresses

```console
uvx norwegian-fake-data wallet --chain ethereum --count 5
uvx norwegian-fake-data wallet --chain bitcoin --seed 42 --unique --count 10
uvx norwegian-fake-data wallet --chain monero --format json
```

`--chain` is required. All three profiles preserve recognizable mainnet prefixes
and lengths, and deliberately insert one character outside the format's alphabet:

| Chain | Supported appearance | Deliberate invalidity |
| --- | --- | --- |
| Ethereum | `0x` plus 40 characters (42 total) | One `g` in the body, outside hexadecimal |
| Bitcoin | SegWit P2WPKH `bc1q…` (42 total) | One `b` in the body, outside Bech32 |
| Monero | Standard `4…` (95 total) | One `0` in the body, outside Monero Base58 |

The forbidden character is always inside the body; strict address decoding fails.
These are fictional display strings, not usable addresses. Random valid addresses,
burn addresses, and incorrect Ethereum checksum capitalization do not provide this
guarantee. No private keys are generated, and no blockchain access is performed.
Other Bitcoin address types and Monero subaddresses/integrated addresses are not
currently supported.

Use `--count`, `--seed`, `--unique`, and `--format rich|plain|json|csv` as with
other identifiers. JSON/CSV include `address`, `chain`, `address_type`,
`fictional_method`, `invalid_reason`, `source_url`, and `verified_on`.

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
These default Norwegian prefixes were absent from Statens vegvesen's published plate series when
checked on 2026-10-06; they are not an officially reserved film range.

### US and UK plates

Choose `--locale no|us|uk`; `no` remains the default. The international profiles
deliberately break a documented allocation rule while keeping the familiar plate
layout. There is no valid-number mode and no fallback to unchecked random plates.
For example:

```console
uvx norwegian-fake-data plate --locale us --state CA --count 10 --unique --seed 73
uvx norwegian-fake-data plate --locale uk --region gb \
  --registered-on 2022-04-18 --as-of 2026-11-02 --count 10 --seed 73
uvx norwegian-fake-data plate --locale uk --as-of 2026-11-02 --format json
```

US plates require an explicit state. **California (`CA`) is currently the only
supported state.** Its seven-character passenger-car profile looks like
`2SAM123`, using only `SAM`, `FAN`, or `GAT` for the letter block. California DMV
explicitly deletes those combinations from regular series and personalized plates.
They are not an official film reservation. There are 27,000 unique combinations.
The profile uses the familiar legacy layout introduced in 1980, not a simulation
of newly issued 2026 plates or their chronological serial ranges. `--as-of` must
be in 1980 or later. Other states, including NY and TX, are rejected until a
documented fictional construction is available.

UK plates currently support **Great Britain (`gb`: England, Scotland, Wales)**.
The region defaults to `gb`; Northern Ireland (`ni`) is explicitly unsupported.
Values look like `ZZ22 ABC`: `ZZ` is deliberately invalid because DVLA prohibits
`Z` in the first two positions of current-style registrations. The serial letters
otherwise follow the published restrictions, excluding `I` and `Q`.

The two-digit age identifier follows the vehicle's `--registered-on` date:
March–August 2026 gives `26`, September 2026–February 2027 gives `76`, and so on.
It does not use a character's birthday. Registration defaults to `--as-of`, which
defaults to today, and cannot be after the story date. Supported registration
dates are 2001-09-01 through 2050-08-31; older styles and the later age-code cycle
are rejected. Each registration period has 13,824 unique fictional plates.

`--count`, `--seed`, `--unique`, `--compact`, and all output formats work for both
profiles. `--prefix` remains Norwegian-only so the invalid international letter
blocks cannot be overridden. `--state` is US-only; `--region` and
`--registered-on` are UK-only. Invalid option combinations fail before output.
Use a fixed `--as-of` for reproducible GB plate dates and structured plate records.

Plate JSON/CSV now includes `locale`, `state`, `region`, `vehicle_class`,
`plate_style`, `registered_on`, `as_of`, `fictional_method`, `invalid_reason`,
source URLs, and the rule verification date. Plain output remains one plate per
line. The existing Python `generate_plates()` still returns strings with unchanged
Norwegian seeded results; `generate_plate_records()` returns the full provenance.
These profiles describe passenger-car registration text, not rendered plate artwork
or a guarantee that an unrelated jurisdiction could never use the same text.

## US Social Security and UK National Insurance numbers

The standalone `ssn` and `nino` commands always generate deliberately invalid
values. They do not need a locale, birthday, or gender, and support `--count`,
`--seed`, `--unique`, `--compact`, and the existing output formats:

```console
uvx norwegian-fake-data ssn --count 10 --unique --seed 73
uvx norwegian-fake-data ssn --compact --format csv
uvx norwegian-fake-data nino --count 10 --unique --seed 73
uvx norwegian-fake-data nino --compact --format json
```

SSNs have the shape `000-42-7318` (compact: `000427318`). The `000` prefix is
never allocated; SSA specifically recommends it for fictional displays. The
remaining six digits are sampled without any connection to age or state.

National Insurance numbers have the shape `QQ 12 34 56 C` (compact: `QQ123456C`).
The suffix is A, B, C, or D, but `QQ` is impossible under HMRC prefix rules and
is used in official examples. In unique batches the six-digit body also stays
unique, rather than reusing a number with a different suffix. Both generators
have a one-million-body pool and obey the shared maximum batch size of 100,000.

JSON/CSV includes the number as a string, locale, fictional method, invalidity
reason, source URL, and verification date. Plain output is one identifier per
line; SSN leading zeros are preserved. These prop values intentionally fail real
identifier validation. There is no option to choose an allocated prefix.

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

`person --locale no` explicitly selects the current Norwegian character record.
`person --locale us` and `person --locale uk` fail with an explanation: full
international records still need country-specific schemas and identifier
integration. Use `ssn`, `nino`, international `phone`, and `plate` independently;
changing `--name-locale` continues to affect names only.

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
from norwegian_fake_data import generate_ninos, generate_plate_records, generate_ssns
from norwegian_fake_data import generate_phone_records, generate_wallet_addresses

names = generate_names(10, age=70, as_of=date(2026, 10, 21), category="female", seed=73)
us_names = generate_names(
    10, age=42, as_of=date(2026, 11, 2), name_locale="us", background="higher", seed=73
)
phones = generate_phones(5, seed=42, unique=True)
us_phones = generate_phones(5, locale="us", area_code="415", seed=42)
uk_phones = generate_phones(5, locale="uk", international=True, seed=42)
phone_records = generate_phone_records(5, locale="uk", kind="landline", city="london")
wallets = generate_wallet_addresses(10, chain="ethereum", seed=42, unique=True)
plates = generate_plates(5, seed=42, prefix="QA")
records = generate_fnrs(age=35, as_of=date(2026, 10, 6), seed=42)
characters = generate_people(6, age=42, seed=73, vehicle=True, unique=True)
ssns = generate_ssns(5, seed=73, unique=True)
ninos = generate_ninos(5, seed=73, compact=True)
california_plates = generate_plates(5, locale="us", state="CA", seed=73)
gb_plates = generate_plate_records(
    5,
    locale="uk",
    registered_on=date(2022, 4, 18),
    as_of=date(2026, 11, 2),
    seed=73,
)

print(records[0].fnr, records[0].birthday)
```

`generate_phones()` and `generate_wallet_addresses()` return strings.
`generate_phone_records()` and `generate_wallet_address_records()` return frozen
records with provenance (the latter is also exported from `norwegian_fake_data`).
The international phone and wallet APIs above are available from version 0.5.0.

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
- [NANPA fictional 555 range](https://nanpa.com/numbering/555-line-numbers): US fictional lines.
  Reviewed area codes come from [NANPA's annual report](https://www.nationalnanpa.com/reports/2015_NANPA_Annual_Report.pdf)
  and [California CPUC's area-code table](https://www.cpuc.ca.gov/AreaCodes/).
- [Ofcom drama numbers](https://www.ofcom.org.uk/phones-and-broadband/phone-numbers/numbers-for-drama): UK mobile and geographic profiles.
- [Ethereum API address format](https://ethereum.github.io/execution-apis/api/methods/eth_accounts/),
  [Bitcoin BIP-173](https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki),
  and [Monero standard addresses](https://docs.getmonero.org/public-address/standard-address/):
  address lengths, prefixes, and encoding alphabets. International phone and wallet
  rules were reviewed on 2026-11-02 and are bundled for offline use.
- [Statens vegvesen's plate series](https://www.vegvesen.no/kjoretoy/eie-og-vedlikeholde/skilt/skiltserier/): plate format and prefix selection.
- [SSA fictional-number guidance](https://secure.ssa.gov/apps10/poms.nsf/links/0110201020): `000`-prefixed SSNs.
- [HMRC National Insurance number rules](https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim39110): impossible `QQ` prefix and A–D suffixes.
- [California DMV restricted combinations](https://www.dmv.ca.gov/portal/handbook/vehicle-industry-registration-procedures-manual-2/special-plates/personalized-configurations-mandatory-refusal/): deleted `SAM`, `FAN`, and `GAT` letter blocks.
  [DMV plate history](https://www.dmv.ca.gov/portal/uploads/2022/06/VR-Manual-Appendix-1E-accessible-5-2022.pdf): the legacy passenger layout.
- [DVLA registration styles](https://dvlaregistrations.dvla.gov.uk/help/): prohibited regional letters and permitted serial letters.
  [DVLA INF104](https://www.gov.uk/government/publications/vehicle-registration-numbers-and-number-plates): registration-age identifiers.
  International identifier and plate rules were reviewed on 2026-11-02 and are
  bundled as code constants; generation performs no network or allocation lookups.
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
tagging that commit. For version `0.5.0`:

```console
git tag -a v0.5.0 -m "Release 0.5.0"
git push origin v0.5.0
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

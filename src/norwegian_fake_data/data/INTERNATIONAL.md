# International name data

`names-us.json.gz` and `names-england.json.gz` contain adapted public aggregate
statistics and curated surname weights. They are bundled for offline use. Code
is MIT; each dataset retains its source license and attribution below.

Snapshot version: `2026-11-02.1`. The manifests inside the snapshots record source
URLs, SHA-256 checksums over the input files, retrieval date, geography, and
licenses. `retrieval_url` records archived acquisition URLs where applicable.
An archive's HTTP content encoding is decoded before hashing the XLSX/ZIP payload.

## United States

- **Social Security Administration:** national baby names, 1880–2025, downloaded
  as `ssa.zip` from https://www.ssa.gov/oact/babynames/names.zip.
  Source information: https://www.ssa.gov/oact/babynames/background.html.
  US federal government data; SSA's national dataset is catalogued under CC0:
  https://catalog.data.gov/dataset/baby-names-from-social-security-card-applications-national-data.
  Changes: selected name/category/year/count rows; converted counts to integer
  sampling weights; compressed JSON. Suppressed counts below five are absent;
  no zeros were invented. SSA removes spaces/hyphens and does not clean placeholder
  names. Early cohorts are incomplete. This archive was acquired through the
  Internet Archive because direct SSA downloads returned HTTP 403. Its SHA-256 is
  `cd78e975ed7bb358e018dd62fbe14ced89295e9581c49172ca4eedcb011b3724`.
- **US Census Bureau:** Frequently Occurring First Names and Last Names in the
  2020 Census, released 14 April 2026:
  https://www.census.gov/topics/population/genealogy/data/2020_names.html.
  Input `census-2020.xlsx` is the full surname file **with negative-number removal**:
  https://www2.census.gov/topics/genealogy/2020surnames/Names2020_LastNames_RaceHispanic.xlsx.
  US federal government data. Changes: selected the 156,621 named, ranked rows and
  positive total counts; converted uppercase labels to title case; omitted
  aggregate rows; compressed JSON. These frequencies include disclosure-avoidance
  adjustments and describe the population, not birth cohorts or income classes.
- **Weiss, Deborah M., Matthew Spitzer, and Ethan Nourbash (2026):** First Names
  Dataset: Race and Socioeconomic Status (SES) Signals, v1.0, Harvard Dataverse,
  https://doi.org/10.7910/DVN/Q3V8OS. License: CC BY 4.0,
  https://creativecommons.org/licenses/by/4.0/.
  `ses.csv`: https://dataverse.harvard.edu/api/access/datafile/14345029?format=original.
  `ses-readme.txt`: https://dataverse.harvard.edu/api/access/datafile/14347278?format=original.
  Changes: selected canonical name/SNI for `clean` and `combined_only` stems with
  spellings shorter than 11 characters; case-folded matching keys; omitted ambiguous
  stem groups and potentially truncated spellings; compressed JSON. Runtime joins
  only exact case-insensitive canonical spellings to SSA names, retaining SSA counts.
  Scores pool 1982–2017 California births. SNI is average residential ZIP-code income
  percentile; its core sample excludes births coded Hispanic or Asian. It is neither
  household income nor current adult income, and cannot recover income-conditioned
  name frequencies. BNI and racial proportions are not used for generation.

Analyses, interpretations, or conclusions reached regarding the birth, death, or
fetal death data are credited to the authors and not to the California Department
of Public Health. The underlying individual birth records are not distributed.

## England profile

**Office for National Statistics (ONS).** Contains public sector information
licensed under the Open Government Licence v3.0:
https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/.
The source geography is **England and Wales**. This is not an England-only or
whole-UK population model.

- Annual names: combined 1996–2021 workbook, supplemented with the complete
  name/count lists in the 2022, 2023, and 2024 girls/boys workbooks.
  https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesinenglandandwalesfrom1996/1996tocurrent
  https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesenglandandwalesbabynamesstatisticsgirls
  https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesenglandandwalesbabynamesstatisticsboys
  The bundled, verified annual coverage is **1996–2024**, regardless of the current
  landing page's advertised range. Some files were acquired from archived official
  downloads; they may predate subsequent revisions. The exact payload hashes and
  acquisition URLs are in the manifest. Changes: selected annual counts, trimmed
  surrounding name whitespace, omitted suppressed/missing/nonpositive cells.
- Historical top-100 names, 1904–2024 at ten-year intervals:
  https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesenglandandwalestop100babynameshistoricaldata.
  Changes: selected ranked names, trimmed surrounding whitespace, assigned heuristic
  integer weights `1_000_000 // rank`; these are **not published birth counts**.
- Names by parental occupational class, 2001–2024:
  https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/adhocs/2958babynamesbynationalstatisticssocioeconomicclassificationenglandandwales2001to2024.
  Changes: selected all 14 class/category sheets; retained positive published counts
  by year; title-cased uppercase labels; compressed JSON. All nine workbook notes
  are retained. Approximately 10% of records receive NS-SEC codes; the higher of two
  parental classes is used; students and never-worked/long-term-unemployed categories
  are excluded. Counts below three are suppressed. Seven original classes are kept;
  the optional lower/middle/higher grouping combines 5–7 / 3–4 / 1–2 respectively.

**Faker:** 500 British surname weights adapted from the `en_GB` person provider,
commit `685ea97a9fbb4ab36dc32ea4d318498992f7ba7e`:
https://github.com/joke2k/faker/blob/685ea97a9fbb4ab36dc32ea4d318498992f7ba7e/faker/providers/person/en_GB/__init__.py.
License: MIT; the full copyright and permission notice is in [FAKER-LICENSE.txt](FAKER-LICENSE.txt).
Changes: parsed surname/weight literals without executing source code; multiplied
weights by 100 and rounded to positive integers; compressed JSON. These are curated
British weights with unverified population provenance, not current England census
statistics. No snapshot year or background breakdown is claimed. No Faker runtime
dependency is needed.

## Refreshing

1. Run `uv sync --locked` to install the development XLSX reader.
2. Download the inputs to a cache directory using the URLs in the `SOURCES` mapping
   in `scripts/update_international_names.py`. Use those mapping keys as filenames.
   `ons-annual.xlsx` is the 1996–2021 combined workbook, and
   `ons-{girls,boys}-{2022,2023,2024}.xlsx` are the full annual workbooks.
   `ons-historical.xlsx`, `ons-nssec.xlsx`, `faker-en-gb.py`, and `faker-license.txt`
   complete the England inputs. Preserve the pinned Faker revision.
3. Optionally create `retrievals.json` in the cache: an object mapping each cached
   filename to its actual acquisition URL, including archive captures. The source
   URL is retained separately. Decode HTTP gzip content encoding before saving a
   workbook/archive; do not save an HTML download error as an input file.
4. Run `uv run python scripts/update_international_names.py --source-dir DIR`.
   The builder validates distributions and records new input hashes. To extend
   coverage, update source filenames, explicit coverage checks, tests, documentation,
   and the dataset version in the builder. Review all source and license changes.
5. Run pytest, Ruff, and the package build. Check both snapshots and the attribution
   files are included in the wheel. No import-time or generation-time downloads occur.

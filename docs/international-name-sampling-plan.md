# Plan: US and England name sampling

Research checked: 2 November 2026. Original proposal, with implementation notes below.

Implementation note (version 0.3.0): the locale and background features described
below are now implemented. Verified bundled ONS annual files cover 1996–2024;
the combined workbook actually ends in 2021, so separate 2022–2024 files supplement
it. US surnames use the 2020 snapshot only. See README.md for the shipped interface
and src/norwegian_fake_data/data/INTERNATIONAL.md for exact source provenance.

## Recommendation

Add US and England name profiles to the existing offline, age-aware name sampler. Add optional socioeconomic **background** profiles, with source-specific explanations. Neither source supports a reliable claim that a generated person is currently poor, middle class, or rich.

Deliver ordinary country sampling first, then socioeconomic options. US age coverage is strong. England has good recent data, but older characters require a deliberately approximate historical mode. Keep the package name and Norwegian defaults.

## Datasets that fit

### US given names: Social Security Administration

Use the [SSA national download](https://www.ssa.gov/oact/babynames/limits.html), covering birth years from 1880; the current site includes 2025. It supplies name, recorded sex, and birth count by year. Sample using counts, not rank or just the top 1,000. Counts below five are suppressed. Historical coverage is incomplete, particularly before Social Security existed; spaces and hyphens are removed in the source. See [SSA methodology](https://www.ssa.gov/oact/babynames/background.html).

This closely matches the existing SSB first-name model. It does not contain income. Record the federal source and reuse statement in the data manifest.

### US surnames: 2020 Census

Use the [2020 Census name files](https://www.census.gov/topics/population/genealogy/data/2020_names.html), released April 2026. The complete surname workbook contains 156,621 surnames occurring at least 100 times. Use the published version with negative-number removal, retain positive counts, and document disclosure-avoidance noise. Population surname frequencies are independent of birth cohort and socioeconomic background. Keep the 2010 snapshot as an optional older story-date source, following the current nearest-snapshot convention.

### US socioeconomic overlay: First Names Dataset

The [Weiss, Spitzer, and Nourbash dataset](https://doi.org/10.7910/DVN/Q3V8OS), released October 2026 under CC BY 4.0, is a promising experimental overlay. I downloaded its CSV and checked its README and user guide: it has 7,507 eight-character name stems and 16 variables, including a readable canonical name and Socioeconomic Name Index (SNI).

It summarizes California births in 1982–2017. SNI averages the income percentiles of the residential ZIP codes associated with each name. It measures neighbourhood income at birth, not household earnings or adult wealth. Its core analytic sample excludes births coded Hispanic or Asian; it is not nationally representative. Values pool the full period rather than providing annual weights. Stem collisions and truncated spellings require careful joins. The [accompanying paper](https://link.springer.com/article/10.1007/s41996-026-00207-8) explains the construction.

Use SSA frequencies for generation, with this dataset supplying an optional, explicitly approximate background score. Do not present the SNI overlay as measured name frequencies within income classes.

### England given names: ONS annual and historical files

Use [ONS annual names, 1996–2025](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesinenglandandwalesfrom1996/1996tocurrent). These provide name ranks and counts. The cited series covers **England and Wales**, so a profile requested as England must expose that source geography; it must not claim England-only precision. Check the separate country tables during ingestion for any usable England-only coverage.

For older adults, use [historical top-100 names, 1904–2024](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesenglandandwalestop100babynameshistoricaldata), available at ten-year intervals. This is limited ranked coverage, not a full annual count series. A 50-year-old in a present-day story cannot be sampled accurately from the post-1996 series. Offer an explicit historical approximation using the nearest historical list and a documented rank-weighting heuristic; do not silently give them a 1996 baby name.

ONS content is generally available under OGL v3.0, subject to stated exceptions; preserve attribution and workbook notices.

### England socioeconomic names: ONS NS-SEC workbook

The [ONS names by socioeconomic classification, 2001–2024](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/adhocs/2958babynamesbynationalstatisticssocioeconomicclassificationenglandandwales2001to2024) is the strongest direct fit. I downloaded and inspected the workbook: 14 data sheets cover boys/girls and seven parental occupational classes, with annual name counts. Its notes say approximately 10% of birth records receive NS-SEC codes, names with counts of two or less are suppressed, the higher parental class is used when both are known, and never-worked/long-term-unemployed and full-time-student categories are excluded. Geography is England and Wales.

Sample directly from published counts within year/category/class. Preserve the original seven classes. For convenient three-group backgrounds, propose higher = classes 1–2, middle = 3–4, lower = 5–7; sum counts before normalizing. These are occupational groups, not poor/rich thresholds. See the [NS-SEC definitions](https://www.ons.gov.uk/methodology/classificationsandstandards/otherclassifications/thenationalstatisticssocioeconomicclassificationnssecrebasedonsoc2010).

### England surnames: practical fallback

I did not find an equivalent modern, open ONS surname-frequency release. [ONS's 2025 response](https://www.ons.gov.uk/aboutus/transparencyandgovernance/freedomofinformationfoi/surnamesintheuk) confirms the requested surname statistics were not held.

For the first release, adapt the weighted surname list from [Python Faker's en_GB provider](https://github.com/joke2k/faker/blob/master/faker/providers/person/en_GB/__init__.py), retaining its [MIT notice](https://github.com/joke2k/faker/blob/master/LICENSE.txt). Pin a commit and audit the list's upstream attribution before bundling. Label it a curated British approximation: its weights are not verified current England census counts, have no trustworthy snapshot year, and contain no class breakdown. Bundle the extracted list rather than adding Faker as a runtime dependency. A better licensed population source can replace it later.

## Proposed interface and semantics

Introduce `--name-locale no|us|england`, default `no`, and `--background any|lower|middle|higher`, default `any`. Use the same keyword arguments in Python. Optional `--nssec` selection can expose the original English occupational classes. The words poor/middleclass/rich could later be storytelling aliases, but the canonical API should describe the evidence honestly.

Proposed examples after implementation:

```console
norwegian-fake-data name --name-locale us --age 42 --as-of 2026-11-02 --count 20
norwegian-fake-data name --name-locale england --age 20 --background higher --count 20
norwegian-fake-data name --name-locale england --age 55 --name-fallback historical
```

Default to an error for unsupported birth years or socioeconomic coverage. In particular, the English class workbook does not cover a present-day 40-year-old. Initially reject that combination with an actionable explanation. Let users explicitly choose an unconditioned background fallback; record that the requested background was not applied. Do not apply a modern class distribution to older cohorts silently. Norway should likewise reject non-`any` background requests until a source exists.

For the experimental US overlay, join SSA names to unambiguous canonical spellings first; inspect stem mappings and exclude unresolved/truncated cases. Restrict the first supported background cohorts to 1982–2017. Define lower/middle/higher as SSA-frequency-weighted thirds of matched names ordered by SNI, within the requested year and category. These are relative **name-score groups**, not thirds of households or poverty/wealth thresholds. Publish cutoffs and matched probability mass; reject a distribution if coverage fails a documented threshold. Missing scores must not become zero or default to lower. A mean SNI alone cannot recover `P(name | income class)`.

Surnames remain independent of background. Full names can therefore be culturally mismatched, as with the existing independent first/surname model; class does not provide evidence for surname pairing.

## Implementation sequence

1. **Generalize the current sampler.** In `names.py`, introduce a profile registry and locale-aware loading, distribution caches, coverage checks, and source-year selection. Retain cumulative integer weights, seeded RNG, equal-category behavior, and offline generation. Keep the existing Norwegian snapshot and random draw order to preserve seeded Norwegian results.
2. **Build reproducible importers.** Retain `scripts/update_names.py` as a compatibility entry point and add source-specific SSA, Census, ONS, and surname importers. Use an XLSX reader as a development-only dependency. Bundle separate compressed locale snapshots with a versioned schema, URLs, licenses, retrieval dates, source geography, checksums, coverage, and suppression rules. Generation must never download data.
3. **Ship ordinary US/England sampling.** Add the CLI/Python options and historical England mode. Historical rank weights are an explicit heuristic, for example `1/rank`, normalized once and converted to positive integer weights. Add `sampling_method` so rank-based and count-based results are distinguishable. Curated surnames need a nullable source year instead of an invented census date.
4. **Add background support.** Implement direct ONS occupational-count sampling first. Add the US SNI overlay behind an experimental method label only after measuring joins, excluded stems, score cutoffs, and cohort coverage. Report the applied method and any fallback in exports. Do not claim cross-country background categories are statistically equivalent.
5. **Integrate character records carefully.** `people.py` currently always creates Norwegian FNRs, phones, and plates. If it accepts `--name-locale`, document that it changes names only and can describe a Norwegian character with an international name. Keep full US/England identifier generation outside this proposal; those require separate source work. Remove SSB-specific help text where options become general.
6. **Validate and document.** Test importer fixtures, suppression, country/category isolation, positive weights, deterministic draws, cache keys, all possible birth years in an age request, historical and background fallbacks, stem ambiguity, and JSON/CSV metadata. Check the built wheel contains every snapshot and works offline. Run the existing pytest, Ruff, and package-build checks. Document coverage and examples in the README and per-source attribution file.

New structured metadata should include requested locale/background, actual source geography, applied background, background method, source period or year, approximation reasons, and dataset version. Keep the existing name fields; treat export-schema additions and nullable surname years as documented compatibility changes.

## Release boundary

The first useful release is ordinary US names plus England names with explicit historical and surname approximations. The next adds English occupational-background sampling for 2001–2024 and experimental US neighbourhood-background scoring for 1982–2017. Accurate present-day income-conditioned names, older English class-conditioned cohorts, class-conditioned surnames, and full international person records remain unsupported unless better evidence is obtained.

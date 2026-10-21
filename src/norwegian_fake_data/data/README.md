# SSB name statistics

`names.json.gz` contains adapted statistics from Statistics Norway (SSB):

- Table 10467: https://www.ssb.no/statbank/table/10467
- Table 12891: https://www.ssb.no/statbank/table/12891

Data license: Creative Commons Attribution 4.0 International (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/.
SSB licensing statement: https://www.ssb.no/en/diverse/lisens.
The package's MIT license applies to its code; these statistics retain CC BY 4.0.

Changes: selected first-name percentages and surname counts; omitted suppressed,
missing and zero cells; grouped by source year and first-name category; scaled
percentages by 1,000 into integer sampling weights; compressed as JSON.
SSB labels are preserved, including compound names already present in the data.
First names and surnames are sampled independently.

The snapshot contains retrieval and source update dates, source URLs, source
response checksums, measures, and notes. Refresh with `python scripts/update_names.py`.
The runtime makes no network requests. Source years are 1880–2025 for first names
and 2018–2025 for surnames. The first-name list covers names with at least 200
bearers in the preceding year; figures below four are suppressed. Surname counts
below 200 are suppressed. These are distributions conditional on published data,
not a complete name register. First-name statistics use birth year before 2021
and naming year from 2021 onward. Surname data is not split by birth cohort.

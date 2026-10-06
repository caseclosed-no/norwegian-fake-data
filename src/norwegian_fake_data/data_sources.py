"""Reviewed offline allocations. Source references are in the README."""

VERIFIED_ON = "2026-10-06"
PHONE_SOURCE = (
    "https://nkom.no/telefoni-og-telefonnummer/telefonnummer-og-den-norske-nummerplan/"
    "alle-nummerserier-for-norske-telefonnumre"
)
PHONE_START = 68050000
PHONE_STOP = 68060000  # Exclusive: 10,000 reserved numbers.

PLATE_SOURCE = "https://www.vegvesen.no/kjoretoy/eie-og-vedlikeholde/skilt/skiltserier/"
# Absent from the published regional AND special-purpose series. These are
# intentionally nonstandard prefixes, not officially reserved film plates.
PLATE_PREFIXES = ("QA", "QB", "QC")
PLATE_START = 10000
PLATE_STOP = 100000

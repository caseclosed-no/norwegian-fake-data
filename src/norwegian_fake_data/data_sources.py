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

# These rules are bundled for offline generation; no allocation lookups are made.
INTERNATIONAL_VERIFIED_ON = "2026-11-02"
SSN_SOURCE = "https://secure.ssa.gov/apps10/poms.nsf/links/0110201020"
NINO_SOURCE = "https://www.gov.uk/hmrc-internal-manuals/national-insurance-manual/nim39110"
GB_PLATE_SOURCE = "https://dvlaregistrations.dvla.gov.uk/help/"
GB_PLATE_DATE_SOURCE = (
    "https://www.gov.uk/government/publications/vehicle-registration-numbers-and-number-plates"
)
CA_PLATE_SOURCE = (
    "https://www.dmv.ca.gov/portal/handbook/vehicle-industry-registration-procedures-manual-2/"
    "special-plates/personalized-configurations-mandatory-refusal/"
)
CA_PLATE_STYLE_SOURCE = (
    "https://www.dmv.ca.gov/portal/uploads/2022/06/VR-Manual-Appendix-1E-accessible-5-2022.pdf"
)
# DMV explicitly deletes these from regular series AND personalized plates.
# This is a small neutral subset of the published list, not a film reservation.
CA_PROP_LETTERS = ("SAM", "FAN", "GAT")

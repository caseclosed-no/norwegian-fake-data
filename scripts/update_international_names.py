"""Build offline US/England snapshots from cached public sources.

Run with uv run python scripts/update_international_names.py --source-dir DIR.
See src/norwegian_fake_data/data/INTERNATIONAL.md for download URLs and filenames.
Input checksums and workbook notes are preserved in each snapshot.
"""

import argparse
import ast
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
FAKER_COMMIT = "685ea97a9fbb4ab36dc32ea4d318498992f7ba7e"
SOURCES = {
    "ssa.zip": "https://www.ssa.gov/oact/babynames/names.zip",
    "census-2020.xlsx": (
        "https://www2.census.gov/topics/genealogy/2020surnames/"
        "Names2020_LastNames_RaceHispanic.xlsx"
    ),
    "ses.csv": "https://dataverse.harvard.edu/api/access/datafile/14345029?format=original",
    "ses-readme.txt": "https://dataverse.harvard.edu/api/access/datafile/14347278?format=original",
    "faker-en-gb.py": (
        f"https://raw.githubusercontent.com/joke2k/faker/{FAKER_COMMIT}/"
        "faker/providers/person/en_GB/__init__.py"
    ),
    "faker-license.txt": (
        f"https://raw.githubusercontent.com/joke2k/faker/{FAKER_COMMIT}/LICENSE.txt"
    ),
}
ONS_BASE = "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/"
ONS_BASE += "birthsdeathsandmarriages/livebirths/"
SOURCES.update(
    {
        "ons-annual.xlsx": ONS_BASE + "datasets/babynamesinenglandandwalesfrom1996/"
        "1996tocurrent/babynames1996to2021.xlsx",
        "ons-historical.xlsx": ONS_BASE + "datasets/babynamesenglandandwalestop100babynames"
        "historicaldata/1904to2024/historicalnames2024.xlsx",
        "ons-nssec.xlsx": ONS_BASE + "adhocs/2958babynamesbynationalstatisticssocioeconomic"
        "classificationenglandandwales2001to2024/birthnamesbynssec.xlsx",
    }
)
for year in range(2022, 2025):
    for sex in ("girls", "boys"):
        filename = f"2025{sex}babynames.xlsx" if year == 2025 else f"{sex}names{year}.xlsx"
        SOURCES[f"ons-{sex}-{year}.xlsx"] = (
            ONS_BASE + f"datasets/babynamesenglandandwalesbabynamesstatistics{sex}/"
            f"{year}/{filename}"
        )


def positive(value):
    return isinstance(value, (int, float)) and value > 0 and int(value) == value


def annual_names(workbook):
    """Combined ONS workbook: named count columns, never ranks or suppressed cells."""
    result = defaultdict(list)
    for sheet, category in (("1", "male"), ("2", "female")):
        rows = iter(workbook[sheet].values)
        header = next(row for row in rows if row[0] == "Name")
        columns = [
            (i, int(str(v)[:4]))
            for i, v in enumerate(header)
            if re.fullmatch(r"\d{4} Count", str(v))
        ]
        if not columns:
            raise ValueError("ONS annual workbook has no year/count columns")
        for row in rows:
            if not isinstance(row[0], str):
                continue
            for column, year in columns:
                if positive(row[column]):
                    result[f"{year}:{category}"].append([row[0].strip(), int(row[column])])
    return dict(result)


def recent_names(workbook, year, category):
    """Use the full England-and-Wales name list, not country/regional top tens."""
    for sheet in workbook:
        rows = iter(sheet.values)
        for row in rows:
            labels = [str(v).strip().lower() for v in row]
            if "name" in labels and "count" in labels and "rank" in labels:
                ni, ci = labels.index("name"), labels.index("count")
                values = [
                    [r[ni].strip(), int(r[ci])]
                    for r in rows
                    if isinstance(r[ni], str) and positive(r[ci])
                ]
                if len(values) > 1000:
                    return {f"{year}:{category}": values}
    raise ValueError(f"Missing full name list for {year} {category}")


def historical_names(workbook):
    result = defaultdict(list)
    for sheet, category in (("Table_1", "female"), ("Table_2", "male")):
        rows = iter(workbook[sheet].values)
        header = next(r for r in rows if r[0] == "Rank")
        columns = [(i, int(v)) for i, v in enumerate(header) if isinstance(v, int)]
        for row in rows:
            if not positive(row[0]):
                continue
            for column, year in columns:
                if isinstance(row[column], str) and row[column].strip():
                    result[f"{year}:{category}"].append(
                        [row[column].strip(), 1_000_000 // int(row[0])]
                    )
    return dict(result)


def occupational_names(workbook):
    result = defaultdict(list)
    for number in range(1, 15):
        category = "male" if number <= 7 else "female"
        nssec = (number - 1) % 7 + 1
        rows = iter(workbook[str(number)].values)
        for row in rows:
            columns = [
                (i, int(v)) for i, v in enumerate(row) if isinstance(v, int) and 2001 <= v <= 2024
            ]
            if columns:
                break
        else:
            raise ValueError("Missing NS-SEC year headers")
        next(rows)  # Totals are not names.
        header = next(rows)
        if header[:3] != ("Rank", "Name", "Count"):
            raise ValueError("Unexpected NS-SEC columns")
        for row in rows:
            for column, year in columns:
                if isinstance(row[column], str) and positive(row[column + 1]):
                    result[f"{year}:{category}:{nssec}"].append(
                        [row[column].strip().title(), int(row[column + 1])]
                    )
    return dict(result)


def ses_scores(text):
    """Exact canonical matches only; do not distribute ambiguous stems to spellings."""
    scores = {}
    for row in csv.DictReader(io.StringIO(text)):
        if row["stem_type"] not in ("clean", "combined_only"):
            continue
        name = row["name_canonical"].strip().casefold()
        # An eleven-character source field can contain truncated names.
        if len(name) >= 11:
            continue
        score = float(row["SNI"])
        if not 0 <= score <= 1:
            raise ValueError("SNI outside [0,1]")
        if name in scores:
            raise ValueError(f"Duplicate SES canonical name: {name}")
        scores[name] = score
    return scores


def faker_surnames(text):
    """Read literals using AST; never execute downloaded Python."""
    tree = ast.parse(text)
    provider = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Provider")
    for node in provider.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "last_names" for t in node.targets
        ):
            rows = ast.literal_eval(node.value.args[0])
            return [[n, round(w * 100)] for n, w in rows if w > 0]
    raise ValueError("Missing Faker surname literals")


def source_manifest(directory, filenames):
    retrievals_path = directory / "retrievals.json"
    retrievals = json.loads(retrievals_path.read_text()) if retrievals_path.exists() else {}
    return {
        name: {
            "url": SOURCES[name],
            "retrieval_url": retrievals.get(name),
            "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest(),
        }
        for name in filenames
    }


def workbook(directory, filename):
    return load_workbook(directory / filename, read_only=True, data_only=True)


def write_snapshot(locale, snapshot):
    for section in ("first_names", "surnames", "historical", "occupational"):
        for key, rows in snapshot.get(section, {}).items():
            if not rows or len({n for n, _ in rows}) != len(rows):
                raise ValueError(f"Empty or duplicate distribution: {section}/{key}")
            if any(not n or not isinstance(w, int) or w <= 0 for n, w in rows):
                raise ValueError(f"Invalid weights: {section}/{key}")
    snapshot.update(
        schema_version=1, dataset_version="2026-11-02.1", retrieved_on=date.today().isoformat()
    )
    target = ROOT / f"src/norwegian_fake_data/data/names-{locale}.json.gz"
    target.write_bytes(
        gzip.compress(
            json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0
        )
    )
    print(f"Wrote {target.name}: {target.stat().st_size:,} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.source_dir
    first = defaultdict(list)
    with zipfile.ZipFile(directory / "ssa.zip") as archive:
        for filename in sorted(archive.namelist()):
            if not re.fullmatch(r"yob\d{4}\.txt", filename):
                continue
            for name, sex, count in csv.reader(io.StringIO(archive.read(filename).decode())):
                first[f"{filename[3:7]}:{ {'F': 'female', 'M': 'male'}[sex] }"].append(
                    [name, int(count)]
                )
    census = workbook(directory, "census-2020.xlsx")
    surnames = [
        [r[0].title(), int(r[2])]
        for r in census.active.iter_rows(min_row=4, values_only=True)
        if isinstance(r[0], str) and isinstance(r[1], int) and positive(r[2])
    ]
    write_snapshot(
        "us",
        {
            "geography": "United States",
            "surname_geography": "United States",
            "licenses": ["US federal government data", "CC BY 4.0 (SES overlay)"],
            "sources": source_manifest(
                directory, ("ssa.zip", "census-2020.xlsx", "ses.csv", "ses-readme.txt")
            ),
            "first_names": dict(first),
            "surnames": {"2020": surnames},
            "ses_scores": ses_scores((directory / "ses.csv").read_text()),
            "ses_period": "1982–2017",
            "ses_geography": "California",
        },
    )
    first = annual_names(workbook(directory, "ons-annual.xlsx"))
    for year in range(2022, 2025):
        for sex, category in (("girls", "female"), ("boys", "male")):
            first.update(
                recent_names(workbook(directory, f"ons-{sex}-{year}.xlsx"), year, category)
            )
    for year in range(1996, 2025):
        for category in ("female", "male"):
            if not first.get(f"{year}:{category}"):
                raise ValueError(f"Missing annual names: {year} {category}")
    nssec = workbook(directory, "ons-nssec.xlsx")
    notes = [r[1] for r in nssec["Notes"].values if len(r) > 1 and isinstance(r[0], int)]
    write_snapshot(
        "england",
        {
            "geography": "England and Wales",
            "surname_geography": "Great Britain",
            "licenses": ["Open Government Licence v3.0 (ONS)", "MIT (Faker surnames)"],
            "sources": source_manifest(
                directory, [n for n in SOURCES if n.startswith(("ons-", "faker-"))]
            ),
            "first_names": first,
            "surnames": {"curated": faker_surnames((directory / "faker-en-gb.py").read_text())},
            "historical": historical_names(workbook(directory, "ons-historical.xlsx")),
            "occupational": occupational_names(nssec),
            "occupational_notes": notes,
        },
    )
    (ROOT / "src/norwegian_fake_data/data/FAKER-LICENSE.txt").write_bytes(
        (directory / "faker-license.txt").read_bytes()
    )


if __name__ == "__main__":
    main()

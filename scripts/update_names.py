"""Refresh the bundled SSB snapshot (network access only during maintenance).

Run: python scripts/update_names.py
Or use saved API responses: --source-dir DIR, containing nfd-TABLE-data.json.
"""

import argparse
import gzip
import hashlib
import itertools
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

TABLES = {"10467": ("Fornavn", "PersonerProsent"), "12891": ("Etternavn", "Personer")}
ROOT = Path(__file__).resolve().parents[1]


def fetch(table, measure):
    url = f"https://data.ssb.no/api/v0/no/table/{table}/"
    with urlopen(url, timeout=90) as response:
        metadata = json.load(response)
    query = {
        "query": [
            {
                "code": v["code"],
                "selection": {
                    "filter": "item",
                    "values": [measure] if v["code"] == "ContentsCode" else v["values"],
                },
            }
            for v in metadata["variables"]
        ],
        "response": {"format": "json-stat2"},
    }
    request = Request(
        url, data=json.dumps(query).encode(), headers={"Content-Type": "application/json"}
    )
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def normalize(dataset, name_dimension, measure):
    """Read JSON-stat in dimension order; never infer counts for suppressed cells."""
    axes = []
    for dimension in dataset["id"]:
        index = dataset["dimension"][dimension]["category"]["index"]
        axes.append(sorted(index, key=index.get) if isinstance(index, dict) else index)
    result = {}
    values = dataset["value"]
    for offset, coordinates in enumerate(itertools.product(*axes)):
        cell = dict(zip(dataset["id"], coordinates, strict=True))
        if cell["ContentsCode"] != measure:
            raise ValueError("Unexpected SSB measure")
        value = values.get(str(offset)) if isinstance(values, dict) else values[offset]
        if value is None or value <= 0:
            continue
        code = cell[name_dimension]
        label = dataset["dimension"][name_dimension]["category"]["label"][code]
        if name_dimension == "Fornavn":
            category = {"1": "female", "2": "male"}[code[0]]
            key = f"{cell['Tid']}:{category}"
            # Published percentages have three decimal places; preserve their precision.
            weight = Decimal(str(value)) * 1000
            if weight != weight.to_integral_value():
                raise ValueError("SSB percentage precision changed; review scaling")
        else:
            key = cell["Tid"]
            weight = Decimal(str(value))
        result.setdefault(key, []).append([label, int(weight)])
    if not result or any(not rows for rows in result.values()):
        raise ValueError("Empty name distributions")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path)
    args = parser.parse_args()
    snapshot = {
        "schema_version": 1,
        "retrieved_on": date.today().isoformat(),
        "attribution": "Statistics Norway (SSB)",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "sources": {},
    }
    for table, (dimension, measure) in TABLES.items():
        dataset = (
            json.loads((args.source_dir / f"nfd-{table}-data.json").read_text())
            if args.source_dir
            else fetch(table, measure)
        )
        snapshot["sources"][table] = {
            "url": f"https://www.ssb.no/statbank/table/{table}",
            "api_url": f"https://data.ssb.no/api/v0/no/table/{table}/",
            "updated": dataset["updated"],
            "measure": measure,
            "sha256": hashlib.sha256(json.dumps(dataset, sort_keys=True).encode()).hexdigest(),
            "notes": dataset.get("note", []),
        }
        snapshot["first_names" if table == "10467" else "surnames"] = normalize(
            dataset, dimension, measure
        )
    years = sorted({int(k.split(":")[0]) for k in snapshot["first_names"]})
    for year in years:
        for category in ("female", "male"):
            if f"{year}:{category}" not in snapshot["first_names"]:
                raise ValueError(f"Missing distribution: {year} {category}")
    path = ROOT / "src/norwegian_fake_data/data/names.json.gz"
    data = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode()
    path.write_bytes(gzip.compress(data, mtime=0))
    print(f"Wrote {path} ({path.stat().st_size:,} bytes); first-name years {years[0]}–{years[-1]}")


if __name__ == "__main__":
    main()

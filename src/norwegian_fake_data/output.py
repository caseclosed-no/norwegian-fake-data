"""Rich terminal output and clean, string-preserving exports."""

import csv
import json
import sys
from datetime import date
from enum import StrEnum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class OutputFormat(StrEnum):
    rich = "rich"
    plain = "plain"
    json = "json"
    csv = "csv"


def render(rows: list[dict], *, value_key: str | None, output: OutputFormat | None) -> None:
    """Plain identifiers are one per line; plain records use tab-separated fields."""
    output = output or (OutputFormat.rich if sys.stdout.isatty() else OutputFormat.plain)
    normalized = [
        {key: value.isoformat() if isinstance(value, date) else value for key, value in row.items()}
        for row in rows
    ]
    if output == OutputFormat.json:
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
    elif output == OutputFormat.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(normalized[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)
    elif output == OutputFormat.plain:
        for row in normalized:
            if value_key:
                print(row[value_key])
            else:
                print("\t".join("" if value is None else str(value) for value in row.values()))
    else:
        console = Console()
        if value_key is None:
            for index, row in enumerate(normalized, start=1):
                details = Table.grid(padding=(0, 2))
                details.add_column(style="bold cyan", no_wrap=True)
                details.add_column(overflow="fold")
                for key, value in row.items():
                    details.add_row(
                        key.replace("_", " ").title(), "—" if value is None else str(value)
                    )
                console.print(Panel.fit(details, title=f"Character {index}", border_style="cyan"))
            return
        if value_key == "name":
            # Full provenance stays in JSON/CSV; keep terminal tables readable.
            normalized = [
                {
                    "name": row["name"],
                    "category": row["category"],
                    "locale": row["name_locale"],
                    "source year": str(row["first_name_year"])
                    + ("*" if row["first_name_approximate"] else ""),
                    "background": row["background_applied"],
                }
                for row in normalized
            ]
        elif value_key in ("ssn", "nino", "plate"):
            keys = (value_key, "locale", "state", "region", "fictional_method")
            normalized = [{key: row[key] for key in keys if key in row} for row in normalized]
        table = Table(header_style="bold cyan", show_lines=len(normalized[0]) > 5)
        for key in normalized[0]:
            table.add_column(
                key.replace("_", " ").title(), overflow="fold", no_wrap=key == value_key
            )
        for row in normalized:
            table.add_row(*("—" if value is None else str(value) for value in row.values()))
        console.print(table)

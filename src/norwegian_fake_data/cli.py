"""Command-line entry point."""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
from enum import StrEnum
from typing import Annotated

import typer

from . import __version__
from .common import MAX_COUNT
from .fnr import generate_fnrs
from .identifiers import generate_phones, generate_plates
from .output import OutputFormat, render
from .people import generate_people

app = typer.Typer(
    help="Norwegian fictional data for murder mystery games. Generation works offline.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    add_completion=False,
)

Count = Annotated[
    int, typer.Option("--count", "-n", min=1, max=MAX_COUNT, help="Number of values.")
]
Seed = Annotated[
    int | None, typer.Option(help="Seed for repeatable results in this package version.")
]
Unique = Annotated[
    bool, typer.Option("--unique", help="No duplicate identifiers within this batch.")
]
Format = Annotated[
    OutputFormat | None,
    typer.Option("--format", "-f", help="Default: rich in a terminal, plain when piped."),
]
Birthday = Annotated[
    tuple[int, int, int] | None,
    typer.Option(
        "--birthday", metavar="YEAR MONTH DAY", help="Birth date; mutually exclusive with --age."
    ),
]
Age = Annotated[int | None, typer.Option(min=0, max=200, help="Completed years on --as-of.")]
ExactAge = Annotated[
    bool,
    typer.Option("--exact-age", help="Turn this age on --as-of, instead of a random birthday."),
]
AsOf = Annotated[
    str | None, typer.Option("--as-of", help="Story date YYYY-MM-DD; defaults to today.")
]


class Mode(StrEnum):
    prop = "prop"
    synthetic = "synthetic"


class PhoneStyle(StrEnum):
    spaced = "spaced"
    compact = "compact"


ModeOption = Annotated[
    Mode,
    typer.Option(help="prop: realistic date with invalid checksum; synthetic: month +80."),
]


@contextmanager
def input_errors() -> Iterator[None]:
    try:
        yield
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from None


def parse_reference(value: str | None) -> date:
    if value is None:
        return date.today()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value, flags=re.ASCII):
        raise ValueError("--as-of must be YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("--as-of must be a real calendar date in YYYY-MM-DD format.") from None


def parse_birthday(value: tuple[int, int, int] | None) -> date | None:
    if value is None:
        return None
    try:
        return date(*value)
    except ValueError:
        raise ValueError("--birthday must be a real calendar date: YEAR MONTH DAY.") from None


def show_version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool, typer.Option("--version", callback=show_version, is_eager=True, help="Show version.")
    ] = False,
) -> None:
    pass


@app.command()
def phone(
    count: Count = 1,
    seed: Seed = None,
    unique: Unique = False,
    output: Format = None,
    international: Annotated[bool, typer.Option("--international", help="Include +47.")] = False,
    style: Annotated[PhoneStyle, typer.Option(help="Phone number spacing.")] = PhoneStyle.spaced,
) -> None:
    """Generate numbers from Nkom's reserved TV/film range, 68050000–68059999."""
    with input_errors():
        values = generate_phones(
            count,
            seed=seed,
            unique=unique,
            international=international,
            style=style.value,
        )
    render([{"phone": value} for value in values], value_key="phone", output=output)


@app.command()
def plate(
    count: Count = 1,
    seed: Seed = None,
    unique: Unique = False,
    output: Format = None,
    prefix: Annotated[
        str | None, typer.Option(help="Choose a reviewed prefix: QA, QB, or QC.")
    ] = None,
    compact: Annotated[
        bool, typer.Option("--compact", help="Omit the space before the digits.")
    ] = False,
) -> None:
    """Generate car plates with prefixes absent from the reviewed official series."""
    with input_errors():
        values = generate_plates(count, seed=seed, unique=unique, prefix=prefix, compact=compact)
    render([{"plate": value} for value in values], value_key="plate", output=output)


@app.command()
def fnr(
    birthday: Birthday = None,
    age: Age = None,
    exact_age: ExactAge = False,
    as_of: AsOf = None,
    mode: ModeOption = Mode.prop,
    count: Count = 1,
    seed: Seed = None,
    unique: Unique = False,
    output: Format = None,
) -> None:
    """Generate fødselsnummer; provide either --birthday YEAR MONTH DAY or --age N."""
    with input_errors():
        records = generate_fnrs(
            count,
            birthday=parse_birthday(birthday),
            age=age,
            exact_age=exact_age,
            as_of=parse_reference(as_of),
            mode=mode.value,
            seed=seed,
            unique=unique,
        )
    render([asdict(record) for record in records], value_key="fnr", output=output)


@app.command()
def person(
    birthday: Birthday = None,
    age: Age = None,
    exact_age: ExactAge = False,
    as_of: AsOf = None,
    mode: ModeOption = Mode.prop,
    count: Count = 1,
    seed: Seed = None,
    unique: Unique = False,
    output: Format = None,
    vehicle: Annotated[
        bool, typer.Option("--vehicle", help="Include a fictional car plate.")
    ] = False,
) -> None:
    """Create character records with names, FNRs, phones and example.com emails."""
    with input_errors():
        records = generate_people(
            count,
            birthday=parse_birthday(birthday),
            age=age,
            exact_age=exact_age,
            as_of=parse_reference(as_of),
            mode=mode.value,
            seed=seed,
            unique=unique,
            vehicle=vehicle,
        )
    render([asdict(record) for record in records], value_key=None, output=output)

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
from .identifiers import generate_phones
from .names import generate_names
from .national_ids import generate_ninos, generate_ssns
from .output import OutputFormat, render
from .people import generate_people
from .plates import generate_plate_records

app = typer.Typer(
    help="Fictional Norwegian/US/UK identifiers and international names. Works offline.",
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


class LocaleOption(StrEnum):
    no = "no"
    us = "us"
    uk = "uk"


Locale = Annotated[LocaleOption, typer.Option(help="Identifier locale. Default: no (Norway).")]
Compact = Annotated[bool, typer.Option("--compact", help="Remove standard separators.")]


class Category(StrEnum):
    female = "female"
    male = "male"
    either = "either"


class NameFallbackOption(StrEnum):
    error = "error"
    nearest = "nearest"
    historical = "historical"


CategoryOption = Annotated[
    Category, typer.Option(help="Source first-name category; either uses both.")
]
NameFallback = Annotated[
    NameFallbackOption,
    typer.Option(
        "--name-fallback",
        help="Outside annual coverage: error, nearest, or England historical ranks.",
    ),
]


class NameLocaleOption(StrEnum):
    no = "no"
    us = "us"
    england = "england"


class BackgroundOption(StrEnum):
    any = "any"
    lower = "lower"
    middle = "middle"
    higher = "higher"


class BackgroundFallbackOption(StrEnum):
    error = "error"
    unconditioned = "unconditioned"


NameLocale = Annotated[
    NameLocaleOption,
    typer.Option("--name-locale", help="Name profile only; identifiers stay Norwegian."),
]
Background = Annotated[
    BackgroundOption, typer.Option(help="Birth background proxy, not current income or wealth.")
]
BackgroundFallback = Annotated[
    BackgroundFallbackOption,
    typer.Option("--background-fallback", help="Unsupported background: error or omit its filter."),
]
Nssec = Annotated[
    int | None,
    typer.Option(min=1, max=7, help="England parental occupation class; replaces --background."),
]


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


def parse_optional_date(value: str | None, option: str) -> date | None:
    if value is None:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value, flags=re.ASCII):
        raise ValueError(f"{option} must be YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{option} must be a real calendar date in YYYY-MM-DD format.") from None


def parse_reference(value: str | None) -> date:
    return parse_optional_date(value, "--as-of") or date.today()


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
    compact: Compact = False,
    locale: Locale = LocaleOption.no,
    state: Annotated[str | None, typer.Option(help="US state; verified profile: CA.")] = None,
    region: Annotated[str | None, typer.Option(help="UK region; verified profile: gb.")] = None,
    registered_on: Annotated[
        str | None, typer.Option(help="GB first-registration date YYYY-MM-DD; defaults to --as-of.")
    ] = None,
    as_of: AsOf = None,
) -> None:
    """Generate fictional passenger-car plates for Norway, California, or Great Britain."""
    with input_errors():
        records = generate_plate_records(
            count,
            seed=seed,
            unique=unique,
            prefix=prefix,
            compact=compact,
            locale=locale.value,
            state=state,
            region=region,
            registered_on=parse_optional_date(registered_on, "--registered-on"),
            as_of=parse_reference(as_of),
        )
    render([asdict(record) for record in records], value_key="plate", output=output)


@app.command()
def ssn(
    count: Count = 1,
    seed: Seed = None,
    unique: Unique = False,
    output: Format = None,
    compact: Compact = False,
) -> None:
    """Generate deliberately invalid US Social Security numbers with a 000 prefix."""
    with input_errors():
        records = generate_ssns(count, seed=seed, unique=unique, compact=compact)
    render([asdict(record) for record in records], value_key="ssn", output=output)


@app.command()
def nino(
    count: Count = 1,
    seed: Seed = None,
    unique: Unique = False,
    output: Format = None,
    compact: Compact = False,
) -> None:
    """Generate deliberately invalid UK National Insurance numbers with a QQ prefix."""
    with input_errors():
        records = generate_ninos(count, seed=seed, unique=unique, compact=compact)
    render([asdict(record) for record in records], value_key="nino", output=output)


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
def name(
    birthday: Birthday = None,
    age: Age = None,
    exact_age: ExactAge = False,
    as_of: AsOf = None,
    category: CategoryOption = Category.either,
    name_fallback: NameFallback = NameFallbackOption.error,
    name_locale: NameLocale = NameLocaleOption.no,
    background: Background = BackgroundOption.any,
    nssec: Nssec = None,
    background_fallback: BackgroundFallback = BackgroundFallbackOption.error,
    count: Count = 1,
    seed: Seed = None,
    output: Format = None,
) -> None:
    """Sample Norwegian, US, or England names for a birth year."""
    with input_errors():
        records = generate_names(
            count,
            birthday=parse_birthday(birthday),
            age=age,
            exact_age=exact_age,
            as_of=parse_reference(as_of),
            category=category.value,
            name_fallback=name_fallback.value,
            name_locale=name_locale.value,
            background=background.value,
            nssec=nssec,
            background_fallback=background_fallback.value,
            seed=seed,
        )
    render([asdict(record) for record in records], value_key="name", output=output)


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
    category: CategoryOption = Category.either,
    name_fallback: NameFallback = NameFallbackOption.error,
    name_locale: NameLocale = NameLocaleOption.no,
    background: Background = BackgroundOption.any,
    nssec: Nssec = None,
    background_fallback: BackgroundFallback = BackgroundFallbackOption.error,
    locale: Locale = LocaleOption.no,
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
            category=category.value,
            name_fallback=name_fallback.value,
            name_locale=name_locale.value,
            background=background.value,
            nssec=nssec,
            background_fallback=background_fallback.value,
            locale=locale.value,
        )
    render([asdict(record) for record in records], value_key=None, output=output)

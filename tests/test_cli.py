import csv
import io
import json

import pytest
from typer.testing import CliRunner

from norwegian_fake_data import __version__
from norwegian_fake_data.cli import app

runner = CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--help"],
        ["phone", "--help"],
        ["fnr", "--help"],
        ["plate", "--help"],
        ["person", "--help"],
    ],
)
def test_help(args):
    result = runner.invoke(app, args)
    assert result.exit_code in (0, 2)
    assert "Usage" in result.output


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


@pytest.mark.parametrize(
    "command,args,key",
    [
        ("phone", [], "phone"),
        ("plate", [], "plate"),
        ("fnr", ["--birthday", "2000", "1", "1"], "fnr"),
        ("person", ["--age", "35", "--vehicle"], "fnr"),
    ],
)
@pytest.mark.parametrize("format", ["json", "csv", "plain", "rich"])
def test_all_output_formats(command, args, key, format):
    result = runner.invoke(app, [command, *args, "--count", "3", "--seed", "5", "--format", format])
    assert result.exit_code == 0, result.output
    assert not result.stderr
    if format == "json":
        values = json.loads(result.stdout)
        assert len(values) == 3 and all(isinstance(row[key], str) for row in values)
        if key == "fnr" and command == "fnr":
            assert values[0][key].startswith("010100")
            assert values[0]["birthday"] == "2000-01-01"
    elif format == "csv":
        values = list(csv.DictReader(io.StringIO(result.stdout)))
        assert len(values) == 3 and key in values[0]
    elif format == "plain":
        assert len(result.stdout.splitlines()) == 3
    else:
        assert key.title() in result.stdout
    if format != "rich":
        assert "\x1b[" not in result.stdout


def test_default_piped_output_is_plain():
    result = runner.invoke(app, ["phone", "--count", "2", "--style", "compact"])
    assert result.exit_code == 0
    assert all(line.isdigit() and len(line) == 8 for line in result.stdout.splitlines())


def test_exact_age_cli():
    result = runner.invoke(
        app, ["fnr", "--age", "35", "--exact-age", "--as-of", "2026-10-06", "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    row = json.loads(result.stdout)[0]
    assert row["birthday"] == "1991-10-06"
    assert row["age"] == 35 and row["mode"] == "prop" and row["as_of"] == "2026-10-06"


@pytest.mark.parametrize("command", ["fnr", "person"])
def test_valid_mode_is_rejected_by_cli(command):
    result = runner.invoke(app, [command, "--age", "35", "--mode", "valid"])
    assert result.exit_code == 2
    assert not result.stdout
    assert "Invalid value for '--mode'" in result.stderr


@pytest.mark.parametrize("command", ["fnr", "person"])
def test_synthetic_mode_cli(command):
    result = runner.invoke(
        app, [command, "--birthday", "1987", "5", "17", "--mode", "synthetic", "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    row = json.loads(result.stdout)[0]
    assert row["fnr"].startswith("178587")
    assert row["mode"] == "synthetic"


@pytest.mark.parametrize(
    "args,fragment",
    [
        (["fnr"], "exactly one"),
        (["fnr", "--age", "35", "--birthday", "1987", "5", "17"], "exactly one"),
        (["fnr", "--birthday", "2023", "2", "29"], "calendar date"),
        (["fnr", "--birthday", "1987", "5", "17", "--exact-age"], "requires"),
        (["fnr", "--age", "35", "--as-of", "20261006"], "YYYY-MM-DD"),
        (["fnr", "--age", "35", "--as-of", "2026-02-30"], "calendar date"),
        (["fnr", "--age", "35", "--mode", "bogus"], "Invalid"),
        (["phone", "--count", "0"], "Invalid"),
        (["phone", "--count", "10001", "--unique"], "10,000"),
        (["plate", "--prefix", "XX"], "prefix"),
        (["person", "--age", "35", "--count", "10001", "--unique"], "10,000"),
    ],
)
def test_errors_are_stderr_without_partial_data(args, fragment):
    result = runner.invoke(app, args)
    assert result.exit_code == 2
    assert not result.stdout
    assert fragment in result.stderr
    assert "Traceback" not in result.stderr

import importlib.util
import json
from pathlib import Path

from openpyxl import Workbook

MODULE_PATH = Path(__file__).parents[1] / "scripts/update_international_names.py"
spec = importlib.util.spec_from_file_location("update_international_names", MODULE_PATH)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def test_annual_importer_selects_counts_and_omits_suppression():
    book = Workbook()
    book.remove(book.active)
    for sheet in ("1", "2"):
        table = book.create_sheet(sheet)
        table.append(["Notes"])
        table.append(["Name", "2001 Rank", "2001 Count", "2000 Rank", "2000 Count"])
        table.append(["Rare", 100, 3, "[x]", "[x]"])
        table.append(["Common", 1, 500, 1, 400])
        table.append(["Suppressed", "[x]", "[x]", None, 0])
    rows = updater.annual_names(book)
    assert rows["2001:male"] == [["Rare", 3], ["Common", 500]]
    assert rows["2000:female"] == [["Common", 400]]


def test_historical_importer_uses_rank_weights_and_trims_names():
    book = Workbook()
    for title in ("Table_1", "Table_2"):
        table = book.create_sheet(title)
        table.append(["Rank", 1904, 1914])
        table.append([1, "Mary ", "Jane"])
        table.append([2, "Florence", "Ann"])
    rows = updater.historical_names(book)
    assert rows["1904:female"] == [["Mary", 1_000_000], ["Florence", 500_000]]


def test_occupational_importer_keeps_classes_years_and_categories_separate():
    book = Workbook()
    for number in range(1, 15):
        table = book.create_sheet(str(number))
        table.append(["Notes"])
        table.append([None, 2001, None, None, None, 2002, None])
        table.append(["Total", None, 100, None, "Total", None, 200])
        table.append(["Rank", "Name", "Count", None, "Rank", "Name", "Count"])
        table.append([1, "ANNA", number + 3, None, 1, "LILY", 30])
        table.append([2, "SUPPRESSED", "[x]", None, None, None, None])
    rows = updater.occupational_names(book)
    assert rows["2001:male:1"] == [["Anna", 4]]
    assert rows["2001:female:7"] == [["Anna", 17]]
    assert rows["2002:female:7"] == [["Lily", 30]]


def test_ses_importer_avoids_ambiguous_stems_and_truncations():
    rows = updater.ses_scores(
        "name_canonical,stem_type,SNI\nAnna,clean,0.4\nElizabeth,combined_only,0.6\n"
        "Alexander,multiple_names_mixed_sex,0.5\nLongtruncat,clean,0.3\n"
    )
    assert rows == {"anna": 0.4, "elizabeth": 0.6}


def test_surname_importer_reads_literals_without_executing_code():
    text = """raise RuntimeError("Never execute this")
class Provider:
    last_names = OrderedDict((("Smith", 1.15), ("Jones", .8)))
"""
    assert updater.faker_surnames(text) == [["Smith", 115], ["Jones", 80]]


def test_source_checksums_are_over_original_bytes(tmp_path):
    (tmp_path / "ses.csv").write_bytes(b"name,SNI\nAnna,0.4\n")
    manifest = updater.source_manifest(tmp_path, ["ses.csv"])
    assert len(manifest["ses.csv"]["sha256"]) == 64
    assert "dataverse.harvard.edu" in manifest["ses.csv"]["url"]
    json.dumps(manifest)

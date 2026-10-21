"""Protect the SSB import boundary: dimensions, suppression, and precision."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "update_names", Path(__file__).resolve().parents[1] / "scripts/update_names.py"
)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def first_name_dataset(values):
    return {
        "id": ["Tid", "ContentsCode", "Fornavn"],
        "dimension": {
            "Tid": {"category": {"index": {"1900": 0, "1901": 1}}},
            "ContentsCode": {"category": {"index": ["PersonerProsent"]}},
            # The dict insertion order intentionally differs from its axis order.
            "Fornavn": {
                "category": {"index": {"2B": 1, "1A": 0}, "label": {"1A": "Åse", "2B": "Bjørn"}}
            },
        },
        "value": values,
    }


@pytest.mark.parametrize("values", [[0.315, None, 0, 1.234], {"0": 0.315, "2": 0, "3": 1.234}])
def test_import_preserves_precise_percentages_and_skips_suppression(values):
    assert updater.normalize(first_name_dataset(values), "Fornavn", "PersonerProsent") == {
        "1900:female": [["Åse", 315]],
        "1901:male": [["Bjørn", 1234]],
    }


def test_import_rejects_changed_precision():
    with pytest.raises(ValueError, match="precision changed"):
        updater.normalize(
            first_name_dataset([0.0001, None, None, None]), "Fornavn", "PersonerProsent"
        )


def test_import_preserves_surname_counts():
    dataset = {
        "id": ["Etternavn", "ContentsCode", "Tid"],
        "dimension": {
            "Etternavn": {"category": {"index": ["BERG"], "label": {"BERG": "Berg"}}},
            "ContentsCode": {"category": {"index": ["Personer"]}},
            "Tid": {"category": {"index": ["2024", "2025"]}},
        },
        "value": [12345, None],
    }
    assert updater.normalize(dataset, "Etternavn", "Personer") == {"2024": [["Berg", 12345]]}

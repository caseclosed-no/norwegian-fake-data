"""Offline Norwegian fictional data generators."""

from importlib.metadata import version

from .fnr import FnrRecord, generate_fnrs
from .identifiers import generate_phones, generate_plates
from .names import NameRecord, generate_names
from .people import PersonRecord, generate_people

__version__ = version("norwegian-fake-data")
__all__ = [
    "FnrRecord",
    "PersonRecord",
    "NameRecord",
    "__version__",
    "generate_fnrs",
    "generate_people",
    "generate_names",
    "generate_phones",
    "generate_plates",
]

"""Offline Norwegian fictional data generators."""

from importlib.metadata import version

from .fnr import FnrRecord, generate_fnrs
from .identifiers import generate_phones, generate_plates
from .people import PersonRecord, generate_people

__version__ = version("norwegian-fake-data")
__all__ = [
    "FnrRecord",
    "PersonRecord",
    "__version__",
    "generate_fnrs",
    "generate_people",
    "generate_phones",
    "generate_plates",
]

"""Offline fictional identifiers and international name generators."""

from importlib.metadata import version

from .fnr import FnrRecord, generate_fnrs
from .identifiers import generate_phones, generate_plates
from .names import NameRecord, generate_names
from .national_ids import NinoRecord, SsnRecord, generate_ninos, generate_ssns
from .people import PersonRecord, generate_people
from .phones import PhoneRecord, generate_phone_records
from .plates import PlateRecord, generate_plate_records
from .wallets import WalletAddressRecord, generate_wallet_address_records, generate_wallet_addresses

__version__ = version("norwegian-fake-data")
__all__ = [
    "FnrRecord",
    "PersonRecord",
    "NameRecord",
    "NinoRecord",
    "SsnRecord",
    "PlateRecord",
    "PhoneRecord",
    "WalletAddressRecord",
    "generate_phone_records",
    "generate_wallet_addresses",
    "generate_wallet_address_records",
    "__version__",
    "generate_fnrs",
    "generate_people",
    "generate_names",
    "generate_phones",
    "generate_plates",
    "generate_plate_records",
    "generate_ssns",
    "generate_ninos",
]

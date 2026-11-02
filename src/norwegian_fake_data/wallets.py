"""Recognizable crypto address props with guaranteed invalid character encoding."""

import random
from dataclasses import dataclass
from typing import Literal

from .common import validate_count

Chain = Literal["ethereum", "bitcoin", "monero"]
# prefix, body length, alphabet, forbidden character, address type, specification
PROFILES = {
    "ethereum": (
        "0x",
        40,
        "0123456789abcdef",
        "g",
        "ethereum",
        "https://ethereum.github.io/execution-apis/api/methods/eth_accounts/",
    ),
    "bitcoin": (
        "bc1q",
        38,
        "qpzry9x8gf2tvdw0s3jn54khce6mua7l",
        "b",
        "segwit-p2wpkh",
        "https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki",
    ),
    "monero": (
        "4",
        94,
        "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
        "0",
        "standard",
        "https://docs.getmonero.org/public-address/standard-address/",
    ),
}


@dataclass(frozen=True)
class WalletAddressRecord:
    address: str
    chain: str
    address_type: str
    fictional_method: str
    invalid_reason: str
    source_url: str
    verified_on: str = "2026-11-02"


def generate_wallet_address_records(
    count: int = 1,
    *,
    chain: Chain,
    seed: int | None = None,
    unique: bool = False,
) -> list[WalletAddressRecord]:
    """Sample fictional mainnet-looking strings, never keys or usable addresses."""
    validate_count(count)
    if chain not in PROFILES:
        raise ValueError("wallet chain must be ethereum, bitcoin, or monero.")
    prefix, size, alphabet, forbidden, address_type, source = PROFILES[chain]
    capacity = len(alphabet) ** (size - 1)
    rng = random.Random(seed)
    if unique:
        # Floyd's algorithm: bounded sampling without replacement from huge pools.
        selected: set[int] = set()
        values = []
        for upper in range(capacity - count, capacity):
            candidate = rng.randrange(upper + 1)
            value = upper if candidate in selected else candidate
            selected.add(value)
            values.append(value)
    else:
        values = [rng.randrange(capacity) for _ in range(count)]
    records = []
    for value in values:
        chars = []
        for _ in range(size - 1):
            value, digit = divmod(value, len(alphabet))
            chars.append(alphabet[digit])
        chars.insert(size // 2, forbidden)
        records.append(
            WalletAddressRecord(
                prefix + "".join(chars),
                chain,
                address_type,
                "forbidden_character",
                f"Body contains {forbidden!r}, which is outside this address format's alphabet.",
                source,
            )
        )
    return records


def generate_wallet_addresses(
    count: int = 1,
    *,
    chain: Chain,
    seed: int | None = None,
    unique: bool = False,
) -> list[str]:
    """Return impossible address strings with recognizable prefixes and lengths."""
    return [
        record.address
        for record in generate_wallet_address_records(
            count,
            chain=chain,
            seed=seed,
            unique=unique,
        )
    ]

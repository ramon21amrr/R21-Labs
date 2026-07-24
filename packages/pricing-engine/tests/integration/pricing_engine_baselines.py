"""Versioned canonical hash baselines for LVFI-ENG-004 audit tests."""

from __future__ import annotations

RATE_CASES = (
    (0.0, 0.0),
    (0.5, 0.5),
    (1.0, 1.0),
    (1.5, 1.0),
    (1.0, 1.5),
    (2.5, 1.2),
    (5.0, 3.0),
    (10.0, 10.0),
)

HISTORICAL_ENGINE_VERSION = "1.0.0"
OPERATIONAL_ENGINE_VERSION = "1.0.1"

HISTORICAL_HASHES = {
    (0.0, 0.0): "8051a1b099137b2c56df3733e1e418d9ed9f95df3c35761c42b89b71bb311c75",
    (0.5, 0.5): "21271b4f51985ee5bec7c635dc9a25f15b3f5304571c761fc68fb4ac790e2e9b",
    (1.0, 1.0): "174828b2a00fabb07fedd8621d6ac696695ae006df18f0eeb9296c853e1c0e51",
    (1.5, 1.0): "1b9791d0dd26fbb7bca068d18dc259a5e07ccf6e3fe7ea1bd4a699f59006f10b",
    (1.0, 1.5): "3f271310adaa3ad25689a03f748c8467a2b8b982dcfa0301e9c5c0f6446b1ad9",
    (2.5, 1.2): "4b545f5fb97be85c2adb8d042d601b0ebf53dc4e0acae8408a3e5ceeac6c9210",
    (5.0, 3.0): "f175b1729f579a7048b045c1219f7007c0f51fb6b78b6d7263d62a20c7c42004",
    (10.0, 10.0): "11bdfc2a7addcf241a248f2a6bdfa888e7d4a6aa639095a809f59a11bba5d670",
}

OPERATIONAL_HASHES = {
    (0.0, 0.0): "92dd0e200cfc270a47db68ca5d141886a7a038ae1bffc03f4c9e6d2397d15a55",
    (0.5, 0.5): "124e7b7755c2942af3030ffb4b8a110d11365277f4bfa746026a5ffa3128441b",
    (1.0, 1.0): "e82cdc5a3a6f928e73c5cde10a64cc0193c76dd2877fc72623dffef841eb19d4",
    (1.5, 1.0): "e45ea750576085fa40d3ebfe0cfc7dde86eeb96cd3dddabcdccd0d3617f4cc2c",
    (1.0, 1.5): "94b555c09467c4028e7606885ae12eb7ba49e264fc99dc7cca3bba4329062060",
    (2.5, 1.2): "cee70d41efdc544ec2cc293216d029bd243885dc432fb321bd8b37b7d70ddf10",
    (5.0, 3.0): "034edc8c0112f463332c95ab482083715e1b2e7820a06702f28c30a4b06ba370",
    (10.0, 10.0): "e3c69898066ea218fdf087596b9226602c0f21bb1ec023787755242c2a55ecee",
}

MATHEMATICAL_CHANGE_CASES = ((1.0, 1.0), (1.5, 1.0), (1.0, 1.5))
VERSION_ONLY_CASES = tuple(
    case for case in RATE_CASES if case not in MATHEMATICAL_CHANGE_CASES
)

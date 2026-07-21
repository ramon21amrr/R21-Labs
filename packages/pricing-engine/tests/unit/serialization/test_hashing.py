from lvfi_pricing.core.errors import CalculationError
from lvfi_pricing.domain import Probability
from lvfi_pricing.serialization import canonical_bytes, sha256_canonical


def test_canonical_bytes_are_compact_utf8_and_deterministic() -> None:
    first = canonical_bytes(("ação", Probability(0.1)))
    second = canonical_bytes(("ação", Probability(0.1)))
    assert isinstance(first, bytes)
    assert first == second
    assert not first.startswith(b"\xef\xbb\xbf")
    assert not first.endswith(b"\n")
    assert b" " not in first


def test_sha256_is_lowercase_and_changes_with_content() -> None:
    digest = sha256_canonical(Probability(0.5))
    assert isinstance(digest, str)
    assert len(digest) == 64
    assert digest == digest.lower()
    assert digest != sha256_canonical(Probability(0.1))


def test_hashing_propagates_typed_errors() -> None:
    result = canonical_bytes(object())
    assert isinstance(result, CalculationError)
    assert isinstance(sha256_canonical(object()), CalculationError)

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.serialization import canonical_bytes, sha256_canonical


@given(st.floats(allow_nan=False, allow_infinity=False, width=64))
def test_finite_float_serialization_is_deterministic(value: float) -> None:
    assert canonical_bytes(value) == canonical_bytes(value)
    digest = sha256_canonical(value)
    assert isinstance(digest, str)
    assert len(digest) == 64


@given(st.tuples(st.integers(), st.integers()))
def test_tuple_order_is_semantically_preserved(value: tuple[int, int]) -> None:
    assert (
        canonical_bytes(value) != canonical_bytes(tuple(reversed(value)))
        or value[0] == value[1]
    )

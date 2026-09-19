import pytest

from tests.integration.live_assertions import assert_live_provider


@pytest.mark.live
def test_live_gyftr():
    assert_live_provider("GYFTR", "SWIGGY")

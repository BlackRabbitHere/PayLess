import pytest

from tests.integration.live_assertions import assert_live_provider


@pytest.mark.live
def test_live_easemytrip():
    assert_live_provider("EASEMYTRIP", "EASEMYTRIP")

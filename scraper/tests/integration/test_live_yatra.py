import pytest

from tests.integration.live_assertions import assert_live_provider


@pytest.mark.live
def test_live_yatra():
    assert_live_provider("YATRA", "YATRA")

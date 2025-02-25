import pytest


@pytest.fixture(params=[
    {"expected": False, "user_id": 1},
    {"expected": True, "user_id": 223957535},
    ])
def test_data(request: pytest.FixtureRequest) -> dict[str, bool | int]:
    return request.param

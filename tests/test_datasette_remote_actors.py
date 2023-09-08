from datasette.app import Datasette
import pytest
import json

ENDPOINT_URL = "https://example.com/actors.json?ids=1"


@pytest.fixture
def non_mocked_hosts():
    return ["localhost"]


@pytest.mark.asyncio
@pytest.mark.parametrize("token", (False, True))
@pytest.mark.parametrize("ttl", (False, True))
async def test_remote_actors(httpx_mock, token, ttl):
    httpx_mock.add_response(
        url=ENDPOINT_URL,
        json={
            "1": {"id": 1, "name": "Cleopatra"},
        },
    )
    settings = {"url": ENDPOINT_URL}
    if token:
        settings["token"] = "xyz"
    if ttl:
        settings["ttl"] = 60
    datasette = Datasette(
        memory=True,
        metadata={"plugins": {"datasette-remote-actors": settings}},
    )
    actors = await datasette.actors_from_ids(["1"])
    request = httpx_mock.get_request()
    assert request.url == ENDPOINT_URL
    if token:
        assert request.headers["authorization"] == "Bearer xyz"
    else:
        assert "authorization" not in request.headers
    expected = {
        "1": {"id": 1, "name": "Cleopatra"},
    }
    assert actors == expected
    # Run a second time
    actors = await datasette.actors_from_ids(["1"])
    assert actors == expected
    # With ttl should have run another request, otherwise should not
    num_requests = len(httpx_mock.get_requests())
    if ttl:
        assert num_requests == 1
    else:
        assert num_requests == 2

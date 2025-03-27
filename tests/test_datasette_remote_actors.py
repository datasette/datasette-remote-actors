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
@pytest.mark.parametrize("ids", (["1"], [1]))
async def test_remote_actors(httpx_mock, token, ttl, ids):
    httpx_mock.add_response(
        url=ENDPOINT_URL,
        json={
            "1": {"id": "1", "name": "Cleopatra"},
        },
        is_reusable=True,
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
    actors = await datasette.actors_from_ids(ids)
    request = httpx_mock.get_request()
    assert request.url == ENDPOINT_URL
    if token:
        assert request.headers["authorization"] == "Bearer xyz"
    else:
        assert "authorization" not in request.headers
    expected = {
        "1": {"id": "1", "name": "Cleopatra"},
    }
    assert actors == expected
    # Run a second time
    actors = await datasette.actors_from_ids(ids)
    assert actors == expected
    # With ttl should have run another request, otherwise should not
    num_requests = len(httpx_mock.get_requests())
    if ttl:
        assert num_requests == 1
    else:
        assert num_requests == 2


@pytest.mark.asyncio
async def test_remote_actors_datasette_profiles(httpx_mock):
    httpx_mock.add_response(
        url=ENDPOINT_URL,
        json={
            "1": {"id": "1", "name": "Cleopatra"},
        },
        is_reusable=True,
    )
    settings = {"url": ENDPOINT_URL, "datasette-profiles": True}
    datasette = Datasette(
        metadata={"plugins": {"datasette-remote-actors": settings}},
    )
    await datasette.invoke_startup()
    actors = await datasette.actors_from_ids(["1"])
    assert actors == {"1": {"id": "1", "name": "Cleopatra"}}
    # Now update `profiles` table
    db = datasette.get_internal_database()
    await db.execute_write("insert into profiles (id, name) values (1, 'Cleopatra 2')")
    # Run again
    actors2 = await datasette.actors_from_ids(["1"])
    assert actors2 == {"1": {"id": "1", "name": "Cleopatra 2"}}

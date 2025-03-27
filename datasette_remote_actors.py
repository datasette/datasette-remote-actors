import datasette
from cachetools import TTLCache
import httpx


@datasette.hookimpl
def actors_from_ids(datasette, actor_ids):
    async def inner():
        actors = await _actors_from_ids_remote(datasette, actor_ids)
        if (datasette.plugin_config("datasette-remote-actors") or {}).get(
            "datasette-profiles"
        ):
            # Extend results with extra details from "profiles" table
            db = datasette.get_internal_database()
            profiles = {
                row["id"]: dict(row)
                for row in (
                    await db.execute(
                        "select * from profiles where id in ({})".format(
                            ",".join("?" for _ in actor_ids)
                        ),
                        actor_ids,
                    )
                ).rows
            }
            print("profiles", profiles, "actor_ids", actor_ids)
            for actor_id, profile in profiles.items():
                if actor_id in actors:
                    actors[actor_id].update(
                        {
                            key: value
                            for key, value in profile.items()
                            if value is not None
                        }
                    )
        return actors

    return inner


async def _actors_from_ids_remote(datasette, actor_ids):
    config = datasette.plugin_config("datasette-remote-actors") or {}
    if not config.get("url"):
        return None

    cache = None
    if config.get("ttl"):
        cache = getattr(datasette, "_remote_actors_cache", None)
        if cache is None:
            cache = datasette._remote_actors_cache = TTLCache(
                maxsize=1000, ttl=config["ttl"]
            )

    to_fetch = []
    from_cache = {}
    for actor_id in actor_ids:
        actor_id = str(actor_id)
        if cache is not None and actor_id in cache:
            from_cache[actor_id] = cache[actor_id]
        else:
            to_fetch.append(actor_id)

    if not to_fetch:
        return from_cache

    token = config.get("token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            config["url"],
            params={"ids": ",".join(map(str, to_fetch))},
            headers=headers,
        )
    if response.status_code != 200:
        return None
    actors = response.json()
    if cache is not None:
        for actor_id, actor in actors.items():
            cache[actor_id] = actor
    return {**from_cache, **actors}

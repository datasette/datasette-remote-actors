import datasette
from cachetools import TTLCache
import httpx


@datasette.hookimpl
def actors_from_ids(datasette, actor_ids):
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
        if cache is not None and actor_id in cache:
            from_cache[actor_id] = cache[actor_id]
        else:
            to_fetch.append(actor_id)

    if not to_fetch:
        return from_cache

    # Fetch the remaining actors from the endpoint
    async def inner():
        token = config.get("token")
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["url"], params={"ids": ",".join(to_fetch)}, headers=headers
            )
            if response.status_code != 200:
                return None
            actors = response.json()
            if cache is not None:
                for actor_id, actor in actors.items():
                    cache[actor_id] = actor
            return {**from_cache, **actors}

    return inner

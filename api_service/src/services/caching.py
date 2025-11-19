import json
from functools import wraps
from typing import Callable, Type, TypeVar
import hashlib
from pydantic import BaseModel
from redis.asyncio import Redis

from core.config import settings

ModelT = TypeVar("ModelT", bound=BaseModel)


def redis_cache(
    key_prefix: str,
    model: Type[ModelT],
    single_item: bool = False,
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = args[0]
            redis: Redis = service.redis

            key_payload = json.dumps(kwargs, sort_keys=True, default=str)
            key_suffix = hashlib.md5(key_payload.encode()).hexdigest()
            cache_key = f"{key_prefix}:{key_suffix}"

            cached_data = await redis.get(cache_key)
            if cached_data:
                cached_data = cached_data.decode('utf-8')
                if model:
                    if single_item:
                        return model.model_validate_json(cached_data)
                    return [
                        model.model_validate(item) for item in json.loads(cached_data)
                    ]
                return json.loads(cached_data)

            result = await func(*args, **kwargs)
            if result:
                if single_item:
                    await redis.set(
                        cache_key,
                        result.model_dump_json(),
                        ex=settings.CACHE_EXPIRE_IN_SECONDS,
                    )
                else:
                    data_to_cache = [item.model_dump() for item in result]
                    await redis.set(
                        cache_key,
                        json.dumps(data_to_cache, default=str),
                        ex=settings.CACHE_EXPIRE_IN_SECONDS,
                    )
            return result

        return wrapper

    return decorator

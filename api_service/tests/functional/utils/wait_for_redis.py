import time
import backoff
from redis import Redis
from settings import settings


@backoff.on_exception(backoff.expo, (ConnectionError, Exception), max_time=30)
def wait_for_redis():
    redis = Redis(host=settings.redis_host, port=settings.redis_port)
    try:
        if not redis.ping():
            raise ConnectionError
    finally:
        redis.close()


if __name__ == '__main__':
    wait_for_redis()

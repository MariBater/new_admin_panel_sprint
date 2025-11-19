import time
from redis import Redis
from settings import settings

if __name__ == '__main__':
    redis = Redis(host=settings.redis_host, port=settings.redis_port)
    while True:
        if redis.ping():
            break
        time.sleep(1)

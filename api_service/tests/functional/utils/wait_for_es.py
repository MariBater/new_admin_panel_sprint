import backoff
from elasticsearch import Elasticsearch

from settings import settings


@backoff.on_exception(backoff.expo, (ConnectionError, Exception), max_time=30)
def wait_for_es():
    es_client = Elasticsearch(hosts=settings.es_url)
    try:
        if not es_client.ping():
            raise ConnectionError
    finally:
        es_client.close()


if __name__ == '__main__':
    wait_for_es()

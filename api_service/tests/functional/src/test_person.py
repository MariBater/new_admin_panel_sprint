import pytest
import http

from ..settings import indexes

pytestmark = pytest.mark.asyncio
@pytest.mark.parametrize(
    'path_param, expected_answer',
    [
        (
            {'person_id': 'b45bd7bc-2e16-46d5-b125-983d356768c0'},
            {'status': 200, 'full_name': "Ben"},
        ),
        (
            {'person_id': '12345678-1234-1234-1234-123456789012'},
            {'status': 404, 'full_name': ""},
        ),
        (
            {'person_id': ''},
            {'status': 404, 'full_name': ""},
        ),
    ],
)
async def test_details(make_get_request, es_write_data, path_param, expected_answer):
    for index in indexes:
        await es_write_data(index)
    api_path = f'/persons/{path_param["person_id"]}'

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, {})

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("full_name", "") == expected_answer.get("full_name", "")


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        # 1. Поиск по имени, которое точно есть
        (
            {'query': 'David'},
            {'status': http.HTTPStatus.OK, 'length': 1},
        ),
        # 2. Пустой запрос (необязательный параметр) должен вернуть всех
        (
            {'query': ''},
            {'status': http.HTTPStatus.OK, 'length': 3},
        ),
        # 3. Поиск по имени, которого нет
        (
            {'query': 'Qwerty'},
            {'status': http.HTTPStatus.OK, 'length': 0},
        ),
        # 4. Вывести только N записей (N=10) -> Ожидаем 1, так как в данных всего 1 David
        (
            {'query': 'David', 'page_size': 10},
            {'status': http.HTTPStatus.OK, 'length': 1},
        ),
    ],
)
async def test_search(make_get_request, es_write_data, query_data, expected_answer):
    api_path = '/persons/search'
    for index in indexes:
        await es_write_data(index)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer['status']
    if 'length' in expected_answer:
        assert len(body) == expected_answer['length']


async def test_person_search_cache(make_get_request, es_write_data, es_client):
    """Тест кеширования поиска по персоналиям."""
    api_path = '/persons/search'
    for index in indexes:
        await es_write_data(index)
    query_data = {'query': 'David'}

    await make_get_request(api_path, query_data)  # 1. Заполняем кеш
    await es_client.delete(index='persons', id='b45bd7bc-2e16-46d5-b125-983d356768c0')  # 2. Удаляем из ES
    await es_client.indices.refresh(index='persons')

    cached_body, _, cached_status = await make_get_request(api_path, query_data)  # 3. Повторный запрос
    assert cached_status == http.HTTPStatus.OK
    assert len(cached_body) == 1  # Данные из кеша, несмотря на удаление из ES


@pytest.mark.parametrize(
    'path_param, expected_answer',
    [
        (
            {'person_id': 'b45bd7bc-2e16-46d5-b125-983d356768c0'},
            {'status': 200, 'length': 0},
        ),
        (
            {'person_id': '12345678-1234-1234-1234-123456789012'},
            {'status': 200, 'length': 0},
        ),
        (
            {'person_id': ''},
            {'status': 404, 'length': 1},
        ),
    ],
)
async def test_person_film(
    make_get_request, es_write_data, path_param, expected_answer
):
    api_path = f'/persons/{path_param["person_id"]}/film'
    for index in indexes:
        await es_write_data(index)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, {})

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]
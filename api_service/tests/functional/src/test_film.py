import http

import pytest
from ..settings import film_index

pytestmark = pytest.mark.asyncio
@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        # 1. Поиск по фразе, которая точно есть
        ({'query': 'The Star'}, {'status': http.HTTPStatus.OK, 'length': 1}),
        # 2. Поиск по фразе, которой нет
        ({'query': 'Mashed potato'}, {'status': http.HTTPStatus.OK, 'length': 0}),
        # 3. Вывести только N записей (N=10)
        (
            {'query': 'The Star', 'page_size': 1},
            {'status': http.HTTPStatus.OK, 'length': 1},
        ),
        # 4. Валидация: обязательный параметр query отсутствует
        ({}, {'status': http.HTTPStatus.UNPROCESSABLE_ENTITY}),
    ],
)
async def test_search(make_get_request, es_write_data, query_data, expected_answer):
    api_path = '/films/search'
    await es_write_data(film_index)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer['status']
    if 'length' in expected_answer:
        assert len(body) == expected_answer['length']


async def test_film_search_cache(make_get_request, es_write_data, es_client):
    """Тест кеширования поиска по фильмам."""
    api_path = '/films/search'
    await es_write_data(film_index)
    query_data = {'query': 'The Star'}

    await make_get_request(api_path, query_data)  # 1. Заполняем кеш. ID фильма 'a5a8f573-3ce5-4f30-b252-9f332715b5da'
    await es_client.delete(index='movies', id='a5a8f573-3ce5-4f30-b252-9f332715b5da')  # 2. Удаляем из ES
    await es_client.indices.refresh(index='movies')

    cached_body, _, cached_status = await make_get_request(api_path, query_data)  # 3. Повторный запрос
    assert cached_status == http.HTTPStatus.OK
    assert len(cached_body) == 1  # Данные из кеша, несмотря на удаление из ES


@pytest.mark.parametrize(
    'path_param, expected_answer',
    [
        (
            {'film_id': 'a5a8f573-3ce5-4f30-b252-9f332715b5da'},
            {'status': 200, 'title': "The Star"},
        ),
        (
            {'film_id': '12345678-1234-1234-1234-123456789012'},
            {'status': 404, 'full_name': ""},
        ),
    ],
)
async def test_details(make_get_request, es_write_data, path_param, expected_answer):
    api_path = f'/films/{path_param["film_id"]}'
    await es_write_data(film_index)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, {})

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("title", "") == expected_answer.get("title", "")


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
            {'genre': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f90'}, # Action
            {'status': 200, 'length': 1},
        ),
        (
            {'genre': '12345678-1234-1234-1234-123456789012'},
            {'status': 200, 'length': 0},
        ),
        (
            {'sort': '-imdb_rating'},
            {'status': 200, 'imdb_rating': 8.5},
        ),
        (
            {'sort': 'imdb_rating'},
            {'status': 200, 'imdb_rating': 8.5},
        ),
    ],
)
async def test_films(make_get_request, es_write_data, query_data, expected_answer):
    api_path = '/films'
    await es_write_data(film_index)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    if expected_answer.get("length"):
        assert len(body) == expected_answer["length"]
    if expected_answer.get("imdb_rating"):
        assert body[0].get("imdb_rating", "") == expected_answer.get("imdb_rating", "")
import http

import pytest
from settings import genre_index


@pytest.mark.parametrize(
    'path_param, expected_answer',
    [
        (
            {'genre_id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f90'},
            {'status': http.HTTPStatus.OK, 'name': 'Action'},
        ),
        (
            {'genre_id': '12345678-1234-1234-1234-123456789012'},
            {'status': http.HTTPStatus.NOT_FOUND, 'name': ''},
        ),
    ],
)
@pytest.mark.asyncio
async def test_genre_details(make_get_request, es_write_data, path_param, expected_answer):
    """Тест получения жанра по ID."""
    await es_write_data(genre_index)
    api_path = f'/genres/{path_param["genre_id"]}'

    body, headers, status = await make_get_request(api_path)

    assert status == expected_answer['status']
    if status == http.HTTPStatus.OK:
        assert body.get('name') == expected_answer.get('name')


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({}, {'status': http.HTTPStatus.OK, 'length': 5}),
        (
            {'page_number': 1000, 'page_size': 50},  # Страница за пределами диапазона
            {'status': http.HTTPStatus.OK, 'length': 0},
        ),
        (
            {'page_number': 1, 'page_size': -50},
            {'status': http.HTTPStatus.UNPROCESSABLE_ENTITY},
        ),
    ],
)
@pytest.mark.asyncio
async def test_genre_list(make_get_request, es_write_data, query_data, expected_answer):
    """Тест получения списка жанров."""
    await es_write_data(genre_index)
    api_path = '/genres'

    body, headers, status = await make_get_request(api_path, query_data)

    assert status == expected_answer['status']
    if 'length' in expected_answer:
        assert len(body) == expected_answer['length']


@pytest.mark.asyncio
async def test_genre_cache(make_get_request, es_write_data, es_client):
    """Тест кеширования жанра."""
    genre_id = 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f90'
    api_path = f'/genres/{genre_id}'
    await es_write_data(genre_index)

    # 1. Получаем жанр из API, по id. Он должен попасть в кеш.
    body, headers, status = await make_get_request(api_path)
    assert status == http.HTTPStatus.OK
    assert body['name'] == 'Action'

    # 2. Обновляем запись напрямую в ES.
    await es_client.update(index='genres', id=genre_id, body={'doc': {'name': 'Unexpected'}})
    await es_client.indices.refresh(index='genres')

    # 3. Вновь забираем жанр из API, ожидая, что мы берём его из кэша.
    cached_body, cached_headers, cached_status = await make_get_request(api_path)
    assert cached_status == http.HTTPStatus.OK
    assert cached_body['name'] == 'Action'  # Данные из кеша, не 'Unexpected'


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        # 1. Поиск по фразе, которая точно есть
        ({'query': 'Action'}, {'status': http.HTTPStatus.OK, 'length': 1}),
        # 2. Поиск по фразе, которой нет (граничный случай)
        ({'query': 'NonExistentGenre'}, {'status': http.HTTPStatus.OK, 'length': 0}),
        # 3. Вывести только N записей (N=2)
        ({'query': 'o'}, {'status': http.HTTPStatus.OK, 'length': 5}),
        # 4. Валидация данных: пустой запрос
        ({'query': ''}, {'status': http.HTTPStatus.UNPROCESSABLE_ENTITY}),
    ]
)
@pytest.mark.asyncio
async def test_genre_search(make_get_request, es_write_data, query_data, expected_answer):
    """Тест поиска жанров."""
    await es_write_data(genre_index)
    api_path = '/genres/search/'

    body, headers, status = await make_get_request(api_path, query_data)

    assert status == expected_answer['status']
    if 'length' in expected_answer:
        assert len(body) == expected_answer['length']


@pytest.mark.asyncio
async def test_genre_search_cache(make_get_request, es_write_data, es_client):
    """Тест кеширования поиска по жанрам."""
    await es_write_data(genre_index)
    api_path = '/genres/search/'
    query_data = {'query': 'Action'}

    await make_get_request(api_path, query_data)  # 1. Первый запрос, чтобы заполнить кеш
    await es_client.delete(index='genres', id='ef86b8ff-3c82-4d31-ad8e-72b69f4e3f90') # 2. Удаляем запись из ES
    await es_client.indices.refresh(index='genres')

    cached_body, _, cached_status = await make_get_request(api_path, query_data) # 3. Повторный запрос
    assert cached_status == http.HTTPStatus.OK
    assert len(cached_body) == 1  # Данные должны взяться из кеша, несмотря на удаление из ES
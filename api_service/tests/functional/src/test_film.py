import pytest

from functional.testdata.films import generate_film, generate_films


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'query': 'The Star'}, {'status': 200, 'length': 50}),
        ({'query': 'Mashed potato'}, {'status': 200, 'length': 0}),
    ],
)
@pytest.mark.asyncio
async def test_search(make_get_request, es_write_data, query_data, expected_answer):

    api_path = '/api/v1/films/search'
    # 1. Генерируем данные для ES
    films = generate_films()
    bulk_query = [
        {'_index': 'movies', '_id': film['id'], '_source': film} for film in films
    ]

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]


@pytest.mark.parametrize(
    'path_param, expected_answer',
    [
        (
            {'film_id': 'fb111f22-121e-44a7-b78f-b19191810000'},
            {'status': 200, 'title': "The Star"},
        ),
        (
            {'film_id': '12345678-1234-1234-1234-123456789012'},
            {'status': 404, 'full_name': ""},
        ),
    ],
)
@pytest.mark.asyncio
async def test_details(make_get_request, es_write_data, path_param, expected_answer):

    api_path = f'/api/v1/films/{path_param["film_id"]}'
    # 1. Генерируем данные для ES
    film = generate_film()
    bulk_query = [{'_index': 'movies', '_id': film['id'], '_source': film}]

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, {})

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("title", "") == expected_answer.get("title", "")


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
            {'genre': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f90'},
            {'status': 200, 'length': 50},
        ),
        (
            {'genre': '12345678-1234-1234-1234-123456789012'},
            {'status': 200, 'length': 0},
        ),
        (
            {'sort': '-imdb_rating'},
            {'status': 200, 'imdb_rating': 10},
        ),
        (
            {'sort': 'imdb_rating'},
            {'status': 200, 'imdb_rating': 1},
        ),
    ],
)
@pytest.mark.asyncio
async def test_films(make_get_request, es_write_data, query_data, expected_answer):

    api_path = '/api/v1/films'
    # 1. Генерируем данные для ES
    films = generate_films()
    bulk_query = [
        {'_index': 'movies', '_id': film['id'], '_source': film} for film in films
    ]

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, query_data)

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    if expected_answer.get("length"):
        assert len(body) == expected_answer["length"]
    if expected_answer.get("imdb_rating"):
        assert body[0].get("imdb_rating", "") == expected_answer.get("imdb_rating", "")

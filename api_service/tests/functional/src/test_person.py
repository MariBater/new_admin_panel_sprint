import pytest
from functional.testdata.films import generate_films
from functional.testdata.person import generate_persons


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
@pytest.mark.asyncio
async def test_details(make_get_request, es_write_data, path_param, expected_answer):
    api_path = f'/api/v1/persons/{path_param["person_id"]}'

    persons = generate_persons()
    films = generate_films()
    bulk_query = [{'_index': 'movies', '_id': f['id'], '_source': f} for f in films]
    bulk_query.extend(
        [{'_index': 'persons', '_id': p['id'], '_source': p} for p in persons]
    )

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, {})

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("full_name", "") == expected_answer.get("full_name", "")


@pytest.mark.parametrize(
    'query_param, expected_answer',
    [
        (
            {'query': 'David'},
            {'status': 200, 'length': 50},
        ),
        (
            {'query': ''},
            {'status': 200, 'length': 50},
        ),
        (
            {'query': 'Qwerty'},
            {'status': 200, 'length': 0},
        ),
    ],
)
@pytest.mark.asyncio
async def test_search(make_get_request, es_write_data, query_param, expected_answer):
    api_path = f'/api/v1/persons/search'

    persons = generate_persons()
    films = generate_films()
    bulk_query = [{'_index': 'movies', '_id': f['id'], '_source': f} for f in films]
    bulk_query.extend(
        [{'_index': 'persons', '_id': p['id'], '_source': p} for p in persons]
    )

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, query_param)

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]


@pytest.mark.parametrize(
    'path_param, expected_answer',
    [
        (
            {'person_id': 'b45bd7bc-2e16-46d5-b125-983d356768c0'},
            {'status': 200, 'length': 10},
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
@pytest.mark.asyncio
async def test_person_film(
    make_get_request, es_write_data, path_param, expected_answer
):
    api_path = f'/api/v1/persons/{path_param["person_id"]}/film'

    persons = generate_persons()
    films = generate_films()
    bulk_query = [{'_index': 'movies', '_id': f['id'], '_source': f} for f in films]
    bulk_query.extend(
        [{'_index': 'persons', '_id': p['id'], '_source': p} for p in persons]
    )

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(api_path, {})

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]

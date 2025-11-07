import pytest

from functional.testdata.films import generate_films


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'query': 'The Star'}, {'status': 200, 'length': 50}),
        ({'query': 'Mashed potato'}, {'status': 200, 'length': 0}),
    ],
)
@pytest.mark.asyncio
async def test_search(make_get_request, es_write_data, query_data, expected_answer):

    # 1. Генерируем данные для ES
    films = generate_films()
    bulk_query = [
        {'_index': 'movies', '_id': film['id'], '_source': film} for film in films
    ]

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API
    body, headers, status = await make_get_request(query_data)

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]

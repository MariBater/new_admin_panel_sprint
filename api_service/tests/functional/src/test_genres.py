import pytest
from functional.testdata.genres import generate_genres

@pytest.mark.asyncio
async def test_get_all_genres(make_get_request, es_with_genres):
    """Тест успешного получения списка всех жанров."""
    # 1. Запрашиваем данные из ES по API
    api_path = "/api/v1/genres/"
    body, headers, status = await make_get_request(api_path, {})

    # 2. Проверяем ответ
    assert status == 200
    genres = es_with_genres["genres"]
    assert len(body) == len(genres)
    assert body[0]["name"] == genres[0]["name"]


# --- Тесты для GET /api/v1/genres/ ---
@pytest.mark.parametrize(
    "path_param, expected_answer",
    [
        (
            {"genre_id": "c91fd50b-0e03-4a64-8e4a-e0313b9c872a"},
            {"status": 200, "name": "Action"},
        ),
        (
            {"genre_id": "12345678-1234-1234-1234-123456789012"},
            {"status": 404, "name": ""},
        ),
        ({"genre_id": ""}, {"status": 404, "name": ""}),
    ],
)
@pytest.mark.asyncio
async def test_get_genre_details(
    make_get_request, es_with_genres, path_param, expected_answer
):
    """Тест получения детальной информации о жанре."""
    # 1. Запрашиваем данные из ES по API
    api_path = f'/api/v1/genres/{path_param["genre_id"]}'
    body, headers, status = await make_get_request(api_path, {})

    # 2. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("name", "") == expected_answer.get("name", "")
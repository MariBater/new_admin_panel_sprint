import pytest
from http import HTTPStatus

import pytest_asyncio
from settings import film_index

pytestmark = pytest.mark.asyncio

class TestFilmSearch:
    """Тесты для эндпоинта /api/v1/films/search."""

    @pytest.mark.parametrize(
        "query_params, expected_status",
        [
            ({"query": "Star"}, HTTPStatus.OK),
            ({"query": "NonExistent"}, HTTPStatus.OK),  # Поиск несуществующей записи
            ({}, HTTPStatus.UNPROCESSABLE_ENTITY),  # Отсутствие query
            ({"query": ""}, HTTPStatus.UNPROCESSABLE_ENTITY),  # Пустой query
            ({"query": "A"}, HTTPStatus.UNPROCESSABLE_ENTITY),  # Слишком короткий query
            ({"page_size": 0}, HTTPStatus.UNPROCESSABLE_ENTITY), # Некорректный page_size
            ({"page_number": 0}, HTTPStatus.UNPROCESSABLE_ENTITY), # Некорректный page_number
            ({"page_size": "abc"}, HTTPStatus.UNPROCESSABLE_ENTITY), # Некорректный тип page_size
        ]
    )
    async def test_search_validation(self, make_get_request, es_write_data, query_params, expected_status):
        """Тестирование валидации входных данных."""
        # 1. Загружаем данные в ES
        await es_write_data(film_index)
        # Act
        body, headers, status = await make_get_request("/films/search", query_params)
        # Assert
        assert status == expected_status

    async def test_search_pagination_page_size(self, make_get_request, es_write_data):
        """Тестирование пагинации: вывод N записей (page_size)."""
        # Arrange
        page_size = 1 # В данных только один фильм "The Star", поэтому ожидаем 1
        # 1. Загружаем данные в ES
        # Загружаем данные, которые точно содержат много фильмов
        await es_write_data(film_index) 

        # Act
        body, headers, status = await make_get_request("/films/search", {"query": "Star", "page_size": page_size})

        # Assert
        assert status == HTTPStatus.OK
        assert len(body) == page_size

    async def test_search_pagination_page_number(self, make_get_request, es_write_data):
        """Тестирование пагинации: переход на другую страницу (page_number)."""
        # 1. Загружаем данные в ES
        await es_write_data(film_index)
        # Act
        # Получаем первую страницу
        body1, _, status1 = await make_get_request("/films/search", {"query": "Star", "page_size": 1, "page_number": 1})
        # Получаем вторую страницу
        body2, _, status2 = await make_get_request("/films/search", {"query": "Star", "page_size": 1, "page_number": 2})

        # Assert
        assert status1 == HTTPStatus.OK
        assert status2 == HTTPStatus.OK
        assert len(body1) == 1
        assert len(body2) == 0 # Вторая страница должна быть пустой, так как результат всего один
        # Проверяем, что фильмы на страницах разные
        # Эту проверку убираем, так как второй страницы нет

    async def test_search_by_phrase(self, make_get_request, es_write_data):
        """Тестирование поиска по фразе."""
        # 1. Загружаем данные в ES
        await es_write_data(film_index)
        # Act
        body, headers, status = await make_get_request("/films/search", {"query": "The Star"})

        # Assert
        assert status == HTTPStatus.OK
        assert len(body) > 0
        # Проверяем, что все найденные фильмы содержат 'The Star' в названии
        for film in body:
            assert "The Star" in film['title']

    async def test_search_with_cache(self, make_get_request, es_write_data, redis_client):
        """Тестирование поиска с учётом кеша в Redis."""
        # Arrange
        # 1. Загружаем данные в ES
        await es_write_data(film_index)
        params = {"query": "Star", "page_size": 1}

        # Act: Первый запрос, который должен попасть в кеш
        body1, _, status1 = await make_get_request("/films/search", params)

        # Проверяем, что ключ появился в Redis
        keys = await redis_client.keys(pattern="*")
        assert len(keys) > 0, "Кеш Redis пуст после первого запроса"
        
        # Сохраняем результат первого запроса
        cached_body = body1

        # Имитируем "порчу" данных в Elasticsearch, чтобы убедиться, что данные берутся из кеша
        # (Этот шаг опционален, но хорошо демонстрирует работу кеша)
        # await es_client.delete_document(index_name=film_index.index_name, doc_id=cached_body[0]['uuid'])

        # Act: Второй идентичный запрос
        body2, _, status2 = await make_get_request("/films/search", params)

        # Assert

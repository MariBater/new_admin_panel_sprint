from typing import Annotated

from fastapi import Query


class PaginationParams:
    """
    Класс-зависимость для параметров пагинации.
    Включает валидацию: номер и размер страницы должны быть больше или равны 1.
    """

    def __init__(
        self,
        page_number: Annotated[int, Query(ge=1, description='Номер страницы')] = 1,
        page_size: Annotated[int, Query(ge=1, le=50, description='Размер страницы')] = 50,
    ):
        self.page_number = page_number
        self.page_size = page_size
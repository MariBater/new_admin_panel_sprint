from abc import ABC, abstractmethod
from typing import Any, Optional


class AsyncCache(ABC):
    """Абстрактный класс для асинхронного кеша."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение по ключу."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire: int):
        """Установить значение по ключу с временем жизни."""
        pass
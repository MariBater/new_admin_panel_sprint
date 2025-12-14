import httpx
from pydantic import BaseModel
from core.config import settings


class AuthClient:
    def __init__(self) -> None:
        pass

    async def login(self, login: str, password: str):
        async with httpx.AsyncClient(base_url=settings.AUTH_SERVICE_API) as client:
            user_data = UserLogin(login=login, password=password).model_dump()
            response = await client.post("/login", json=user_data)

            if response.status_code != 200:
                raise Exception(
                    f"Login failed: {response.status_code}, {response.text}"
                )

            return TokenResponse(**response.json())


class UserLogin(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

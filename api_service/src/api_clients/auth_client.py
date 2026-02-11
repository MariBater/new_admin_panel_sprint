import httpx
from pydantic import BaseModel
from core.config import settings


class AuthClient:
    def __init__(self) -> None:
        pass

    async def check_role(self, access_token: str, user_id: str, role: str):
        async with httpx.AsyncClient(base_url=settings.AUTH_SERVICE_API) as client:

            response = await client.post(
                "/roles/check",
                headers={'Authorization': f'Bearer {access_token}'},
                json={'user_id': user_id, "role_name": role},
            )

            if response.status_code != 200:
                raise Exception(
                    f"Login failed: {response.status_code}, {response.text}"
                )

            return response

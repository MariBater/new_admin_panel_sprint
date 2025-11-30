from datetime import timedelta, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request

from src.schemas.auth import UserRegister, UserLogin, TokenResponse

# Эти сервисные функции нужно будет реализовать с реальной логикой БД
# Пока что это будут заглушки

# ЗАГЛУШКИ СЕРВИСНЫХ ФУНКЦИЙ
# Используем простой словарь для имитации базы данных пользователей
fake_users_db = {}


async def get_user_by_login(login: str):
    print(f"Pretending to fetch user {login} from DB.")
    return fake_users_db.get(login)


async def create_user_in_db(login: str, password_hash: str):
    print(f"Pretending to create user {login} in DB.")
    user = {"id": str(uuid4()), "login": login, "password_hash": password_hash}
    fake_users_db[login] = user
    return user


def verify_password(plain_password, hashed_password):
    # В реальном приложении здесь будет werkzeug.security.check_password_hash или passlib
    # Наша заглушка будет сравнивать "захэшированный" пароль
    return f"hashed_{plain_password}" == hashed_password


def get_password_hash(password):
    # В реальном приложении здесь будет werkzeug.security.generate_password_hash или passlib
    return f"hashed_{password}"


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    # Эта функция уже есть в src.core.dependencies, но для простоты дублируем здесь
    # В идеале ее нужно вынести в общий сервис
    from jose import jwt
    from src.core.config import settings

    to_encode = data.copy()
    # Вычисляем абсолютное время истечения токена
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # jose сама преобразует datetime в timestamp
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# КОНЕЦ ЗАГЛУШЕК

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    # Проверяем, существует ли пользователь
    existing_user = await get_user_by_login(user_data.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this login already exists",
        )
    hashed_password = get_password_hash(user_data.password)
    new_user = await create_user_in_db(user_data.login, hashed_password)
    return {"id": new_user["id"], "login": new_user["login"]}


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(response: Response, user_data: UserLogin):
    user = await get_user_by_login(user_data.login)
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
        )

    access_token = create_access_token(data={"sub": user["login"]})
    response.set_cookie(
        key="refreshToken", value="fake-refresh-token-for-demo", httponly=True
    )
    return {"access_token": access_token}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("refreshToken")
    return


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    return {"access_token": "new-fake-access-token-from-refresh"}
    return {"access_token": access_token}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("refreshToken")
    return


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    return {"access_token": "new-fake-access-token-from-refresh"}
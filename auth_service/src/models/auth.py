from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    login: EmailStr
    password: str


class UserLogin(BaseModel):
    login: EmailStr
    password: str


class UserUpdateCredentials(BaseModel):
    login: EmailStr | None = None
    password: str | None = None


class TokenResponse(BaseModel):
    access_token: str
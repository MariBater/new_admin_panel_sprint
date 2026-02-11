from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    login: str
    email: EmailStr
    password: str
    first_name: str | None
    last_name: str | None
    avatar: str | None
    phone: str | None
    city: str | None


class UserLogin(BaseModel):
    login: str
    password: str


class UserUpdateCredentials(BaseModel):
    login: str
    password: str

from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from db.postgres import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    login: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    roles: Mapped[List["Role"]] = relationship(
        secondary="users_roles", back_populates="users"
    )
    auth_histories: Mapped[List["UserAuthHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __init__(self, login: str, password: str, email: str) -> None:
        self.login = login
        self.password = generate_password_hash(password)
        self.email = email

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def __repr__(self) -> str:
        return f'<User {self.login}>'


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    user: Mapped["User"] = relationship(back_populates="user_profile")

    def __repr__(self) -> str:
        return f'<UserProfile {self.first_name} {self.last_name}>'


class UserAuthHistory(Base):
    __tablename__ = 'users_auth_history'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    auth_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(back_populates="auth_histories")

    def __init__(self, user_agent: str, user_id: uuid.UUID):
        self.user_agent = user_agent
        self.user_id = user_id

    def __repr__(self) -> str:
        return f'<UserAuthHistory {self.auth_date}>'


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship(
        secondary="users_roles", back_populates="roles"
    )

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f'<Role {self.name}>'


class UsersRoles(Base):
    __tablename__ = 'users_roles'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    __table_args__ = (UniqueConstraint('user_id', 'role_id', name='uq_user_role'),)

    def __repr__(self) -> str:
        return f'<UsersRoles user_id={self.user_id} role_id={self.role_id}>'
